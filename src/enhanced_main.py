"""
Enhanced VENDORA Main Application with Fixed Async Support
Integrates the hierarchical flow system with API endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import logging
from typing import Dict, Any
import os
from datetime import datetime
from functools import wraps

# Import the hierarchical flow system
from services.hierarchical_flow_manager import HierarchicalFlowManager
from services.explainability_engine import ExplainabilityEngine

# Import existing services
from agents.email_processor.mailgun_handler import MailgunHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def async_route(f):
    """Decorator to handle async routes in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


class VendoraApp:
    """Main VENDORA application with hierarchical flow integration"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = Flask(__name__)
        CORS(self.app)

        # Core components
        self.flow_manager = None
        self.explainability_engine = None
        self.mailgun_handler = None
        self.initialized = False

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy" if self.initialized else "initializing",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "flow_manager": self.flow_manager is not None,
                    "explainability_engine": self.explainability_engine is not None
                }
            })

        @self.app.route('/api/v1/query', methods=['POST'])
        @async_route
        async def process_query():
            """
            Main endpoint for processing user queries through the hierarchical flow

            Expected JSON body:
            {
                "query": "What were my top selling vehicles last month?",
                "dealership_id": "dealer_123",
                "context": {
                    "user_role": "sales_manager",
                    "preferences": {}
                }
            }
            """
            try:
                data = request.get_json()

                if not data:
                    return jsonify({
                        "error": "No JSON data provided"
                    }), 400

                if not data.get('query') or not data.get('dealership_id'):
                    return jsonify({
                        "error": "Missing required fields: query, dealership_id"
                    }), 400

                # Validate dealership_id format to prevent injection
                dealership_id = data['dealership_id']
                if not dealership_id.replace('_', '').replace('-', '').isalnum():
                    return jsonify({
                        "error": "Invalid dealership_id format"
                    }), 400

                # Process through hierarchical flow with timeout
                result = await asyncio.wait_for(
                    self.flow_manager.process_user_query(
                        user_query=data['query'],
                        dealership_id=dealership_id,
                        user_context=data.get('context', {})
                    ),
                    timeout=30.0  # 30 second timeout
                )

                return jsonify(result)

            except asyncio.TimeoutError:
                return jsonify({
                    "error": "Query processing timed out",
                    "message": "The analysis is taking longer than expected. Please try a simpler query."
                }), 504
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again."
                }), 500

        @self.app.route('/api/v1/task/<task_id>/status', methods=['GET'])
        @async_route
        async def get_task_status(task_id):
            """Get the status of a specific task"""
            try:
                # Validate task_id format
                if not task_id.startswith('TASK-'):
                    return jsonify({
                        "error": "Invalid task ID format"
                    }), 400

                status = await self.flow_manager.get_flow_status(task_id)

                if status:
                    return jsonify(status)
                else:
                    return jsonify({
                        "error": "Task not found"
                    }), 404

            except Exception as e:
                logger.error(f"Error getting task status: {str(e)}")
                return jsonify({
                    "error": "Internal server error"
                }), 500

        @self.app.route('/api/v1/agent/<agent_id>/explanation', methods=['GET'])
        def get_agent_explanation(agent_id):
            """Get detailed explanation of an agent's activities"""
            try:
                # Validate agent_id
                valid_agents = ['orchestrator', 'data_analyst', 'senior_analyst', 'master_analyst']
                if agent_id not in valid_agents:
                    return jsonify({
                        "error": f"Invalid agent_id. Valid agents: {valid_agents}"
                    }), 400

                explanation = self.explainability_engine.get_agent_explanation(agent_id)
                return jsonify(explanation)

            except Exception as e:
                logger.error(f"Error getting agent explanation: {str(e)}")
                return jsonify({
                    "error": "Internal server error"
                }), 500

        @self.app.route('/api/v1/system/overview', methods=['GET'])
        def get_system_overview():
            """Get system-wide overview"""
            try:
                overview = self.explainability_engine.get_system_overview()
                return jsonify(overview)

            except Exception as e:
                logger.error(f"Error getting system overview: {str(e)}")
                return jsonify({
                    "error": "Internal server error"
                }), 500

        @self.app.route('/api/v1/system/metrics', methods=['GET'])
        @async_route
        async def get_metrics():
            """Get system metrics"""
            try:
                flow_metrics = await self.flow_manager.get_metrics()

                return jsonify({
                    "flow_metrics": flow_metrics,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error getting metrics: {str(e)}")
                return jsonify({
                    "error": "Internal server error"
                }), 500

        @self.app.route('/api/v1/webhook/mailgun', methods=['POST'])
        @async_route
        async def mailgun_webhook():
            """Handle incoming emails from Mailgun"""
            try:
                # Process email
                result = await self.mailgun_handler.process_webhook(request)

                # If email contains a query, process it through the flow
                if result.get('contains_query'):
                    query_result = await self.flow_manager.process_user_query(
                        user_query=result['extracted_query'],
                        dealership_id=result['dealership_id'],
                        user_context={
                            "source": "email",
                            "sender": result['sender']
                        }
                    )

                    # Send response via email
                    await self.mailgun_handler.send_insight_email(
                        to=result['sender'],
                        insight=query_result
                    )

                return jsonify({"status": "processed"}), 200

            except Exception as e:
                logger.error(f"Error processing mailgun webhook: {str(e)}")
                return jsonify({
                    "error": "Webhook processing failed"
                }), 500

    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing VENDORA Enhanced Platform")

        try:
            # Initialize hierarchical flow manager
            flow_config = {
                "gemini_api_key": self.config.get('GEMINI_API_KEY'),
                "bigquery_project": self.config.get('BIGQUERY_PROJECT'),
                "quality_threshold": float(self.config.get('QUALITY_THRESHOLD', 0.85)),
                "service_account_path": self.config.get('GOOGLE_APPLICATION_CREDENTIALS')
            }

            self.flow_manager = HierarchicalFlowManager(flow_config)
            await self.flow_manager.initialize()

            # Initialize explainability engine
            self.explainability_engine = ExplainabilityEngine()
            await self.explainability_engine.start()

            # Initialize Mailgun handler if configured
            if self.config.get('MAILGUN_PRIVATE_API_KEY'):
                self.mailgun_handler = MailgunHandler(self.config)

            self.initialized = True
            logger.info("✅ VENDORA Platform initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize platform: {str(e)}", exc_info=True)
            raise

    async def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("🛑 Shutting down VENDORA Platform")

        try:
            if self.flow_manager:
                await self.flow_manager.shutdown()

            if self.explainability_engine:
                await self.explainability_engine.stop()

            logger.info("✅ VENDORA Platform shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Run the Flask application"""
        # Initialize components before starting
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.initialize())
        except Exception as e:
            logger.error(f"Failed to initialize: {str(e)}")
            exit(1)

        # Run Flask app
        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        finally:
            # Cleanup on exit
            loop.run_until_complete(self.shutdown())
            loop.close()


def create_app(config: Dict[str, Any]) -> VendoraApp:
    """Factory function to create VENDORA app"""
    app = VendoraApp(config)
    return app


if __name__ == '__main__':
    # Load configuration from environment
    config = {
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'BIGQUERY_PROJECT': os.getenv('BIGQUERY_PROJECT', 'vendora-analytics'),
        'MAILGUN_PRIVATE_API_KEY': os.getenv('MAILGUN_PRIVATE_API_KEY'),
        'MAILGUN_DOMAIN': os.getenv('MAILGUN_DOMAIN'),
        'MAILGUN_SENDING_API_KEY': os.getenv('MAILGUN_SENDING_API_KEY'),
        'DATA_STORAGE_PATH': os.getenv('DATA_STORAGE_PATH', './data'),
        'QUALITY_THRESHOLD': os.getenv('QUALITY_THRESHOLD', '0.85'),
        'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    }

    # Validate required configuration
    required_keys = ['GEMINI_API_KEY']
    missing_keys = [key for key in required_keys if not config.get(key)]

    if missing_keys:
        print(f"❌ Missing required configuration: {missing_keys}")
        print("Please check your .env file")
        exit(1)

    # Create and run the app
    app = create_app(config)

    print("🚀 Starting VENDORA Enhanced Platform...")
    print("📊 Automotive AI Data Platform with Hierarchical Flow")
    print("🌐 Access at: http://localhost:5001")
    print("\nAPI Endpoints:")
    print("  POST   /api/v1/query              - Process analytical query")
    print("  GET    /api/v1/task/<id>/status   - Get task status")
    print("  GET    /api/v1/agent/<id>/explanation - Get agent explanation")
    print("  GET    /api/v1/system/overview    - System overview")
    print("  GET    /api/v1/system/metrics     - System metrics")
    print("  POST   /api/v1/webhook/mailgun    - Email webhook")

    app.run()
