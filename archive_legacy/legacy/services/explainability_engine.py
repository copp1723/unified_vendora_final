"""
Explainability Engine
Provides visibility, monitoring, and explanations for AI agent activities
Python equivalent of the JavaScript agent visibility monitor
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import websockets
import threading
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of operations performed by agents"""
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    CODE_GENERATE = "code:generate"
    CODE_VALIDATE = "code:validate"
    TEST_RUN = "test:run"
    GIT_COMMIT = "git:commit"
    API_CALL = "api:call"
    DECISION_MADE = "decision:made"
    ERROR = "error"
    INFO = "info"


class Phase(Enum):
    """Agent work phases"""
    INITIALIZING = "initializing"
    PLANNING = "planning"
    ANALYZING = "analyzing"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    COMPLETING = "completing"
    FAILED = "failed"


@dataclass
class Operation:
    """Represents an operation performed by an agent"""
    id: str
    agent_id: str
    type: OperationType
    description: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[int] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "type": self.type.value,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "success": self.success
        }


@dataclass
class AgentActivity:
    """Tracks an agent's current activity"""
    agent_id: str
    phase: Phase
    current_task: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    operations: List[Operation] = field(default_factory=list)
    files_accessed: List[str] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_operation(self, operation: Operation):
        """Add an operation to the activity log"""
        self.operations.append(operation)
        
        # Track file access
        if operation.type in [OperationType.FILE_READ, OperationType.FILE_WRITE]:
            file_path = operation.details.get("file_path")
            if file_path and file_path not in self.files_accessed:
                self.files_accessed.append(file_path)
        
        # Track errors
        if operation.type == OperationType.ERROR or not operation.success:
            self.errors.append({
                "timestamp": operation.timestamp,
                "description": operation.description,
                "details": operation.details
            })
    
    def get_duration(self) -> timedelta:
        """Get activity duration"""
        return datetime.now() - self.start_time
    
    def get_summary(self) -> Dict[str, Any]:
        """Get activity summary"""
        return {
            "agent_id": self.agent_id,
            "phase": self.phase.value,
            "current_task": self.current_task,
            "duration_seconds": self.get_duration().total_seconds(),
            "operations_count": len(self.operations),
            "files_accessed": len(self.files_accessed),
            "errors_count": len(self.errors),
            "success_rate": self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate operation success rate"""
        if not self.operations:
            return 1.0
        
        successful = sum(1 for op in self.operations if op.success)
        return successful / len(self.operations)


class ExplainabilityEngine:
    """
    Engine for monitoring, tracking, and explaining AI agent activities
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.activities: Dict[str, AgentActivity] = {}
        self.operation_history: deque = deque(maxlen=1000)  # Keep last 1000 operations
        self.metrics: Dict[str, Any] = defaultdict(int)
        self.websocket_clients: List[websockets.WebSocketServerProtocol] = []
        self.running = False
        self._operation_id_counter = 0
        
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "websocket_port": 8765,
            "enable_websocket": True,
            "log_to_file": True,
            "log_directory": "logs/agent_activity",
            "retention_days": 7,
            "real_time_updates": True
        }
    
    async def start(self):
        """Start the explainability engine"""
        logger.info("🚀 Starting Explainability Engine")
        self.running = True
        
        # Create log directory if needed
        if self.config["log_to_file"]:
            os.makedirs(self.config["log_directory"], exist_ok=True)
        
        # Start WebSocket server if enabled
        if self.config["enable_websocket"]:
            asyncio.create_task(self._start_websocket_server())
        
        # Start background tasks
        asyncio.create_task(self._metrics_aggregator())
        asyncio.create_task(self._log_cleaner())
        
        logger.info("✅ Explainability Engine started")
    
    async def stop(self):
        """Stop the explainability engine"""
        logger.info("🛑 Stopping Explainability Engine")
        self.running = False
        
        # Close WebSocket connections
        for client in self.websocket_clients:
            await client.close()
        
        # Save current state
        await self._save_state()
        
        logger.info("✅ Explainability Engine stopped")
    
    def start_agent_activity(self, agent_id: str, task: Optional[str] = None) -> str:
        """Start tracking a new agent activity"""
        activity = AgentActivity(
            agent_id=agent_id,
            phase=Phase.INITIALIZING,
            current_task=task
        )
        
        self.activities[agent_id] = activity
        
        # Log the start
        self.log_operation(
            agent_id=agent_id,
            op_type=OperationType.INFO,
            description=f"Agent {agent_id} started" + (f" on task {task}" if task else ""),
            details={"task": task}
        )
        
        return agent_id
    
    def update_agent_phase(self, agent_id: str, phase: Phase):
        """Update agent's current phase"""
        activity = self.activities.get(agent_id)
        if activity:
            activity.phase = phase
            
            self.log_operation(
                agent_id=agent_id,
                op_type=OperationType.INFO,
                description=f"Agent entered {phase.value} phase",
                details={"phase": phase.value}
            )
    
    def log_operation(
        self,
        agent_id: str,
        op_type: OperationType,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        success: bool = True
    ) -> str:
        """Log an agent operation"""
        # Generate operation ID
        self._operation_id_counter += 1
        op_id = f"op_{self._operation_id_counter:06d}"
        
        # Create operation
        operation = Operation(
            id=op_id,
            agent_id=agent_id,
            type=op_type,
            description=description,
            details=details or {},
            duration_ms=duration_ms,
            success=success
        )
        
        # Add to activity
        activity = self.activities.get(agent_id)
        if activity:
            activity.add_operation(operation)
        
        # Add to history
        self.operation_history.append(operation)
        
        # Update metrics
        self._update_metrics(operation)
        
        # Log to file if enabled
        if self.config["log_to_file"]:
            asyncio.create_task(self._log_to_file(operation))
        
        # Send real-time update
        if self.config["real_time_updates"]:
            asyncio.create_task(self._send_realtime_update(operation))
        
        logger.debug(f"[{agent_id}] {op_type.value}: {description}")
        
        return op_id
    
    def log_decision(
        self,
        agent_id: str,
        decision: str,
        reasoning: str,
        options_considered: List[str],
        confidence: float = 1.0
    ):
        """Log an agent's decision-making process"""
        activity = self.activities.get(agent_id)
        if activity:
            decision_info = {
                "decision": decision,
                "reasoning": reasoning,
                "options_considered": options_considered,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            activity.decisions.append(decision_info)
        
        self.log_operation(
            agent_id=agent_id,
            op_type=OperationType.DECISION_MADE,
            description=f"Decision: {decision}",
            details={
                "reasoning": reasoning,
                "options": options_considered,
                "confidence": confidence
            }
        )
    
    def get_agent_explanation(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed explanation of agent's current activity"""
        activity = self.activities.get(agent_id)
        if not activity:
            return {"error": f"No activity found for agent {agent_id}"}
        
        # Analyze operations
        operation_summary = self._analyze_operations(activity.operations)
        
        # Generate explanation
        explanation = {
            "agent_id": agent_id,
            "current_phase": activity.phase.value,
            "current_task": activity.current_task,
            "duration": str(activity.get_duration()),
            "summary": activity.get_summary(),
            "operations": operation_summary,
            "files_modified": activity.files_accessed,
            "decisions": activity.decisions[-5:],  # Last 5 decisions
            "errors": activity.errors,
            "timeline": self._generate_timeline(activity),
            "recommendations": self._generate_recommendations(activity)
        }
        
        return explanation
    
    def _analyze_operations(self, operations: List[Operation]) -> Dict[str, Any]:
        """Analyze operations to provide insights"""
        if not operations:
            return {"total": 0}
        
        # Count by type
        type_counts = defaultdict(int)
        for op in operations:
            type_counts[op.type.value] += 1
        
        # Calculate timings
        total_duration = sum(op.duration_ms or 0 for op in operations)
        avg_duration = total_duration / len(operations) if operations else 0
        
        # Find slow operations
        slow_ops = [
            op for op in operations
            if op.duration_ms and op.duration_ms > 1000
        ]
        
        return {
            "total": len(operations),
            "by_type": dict(type_counts),
            "success_rate": sum(1 for op in operations if op.success) / len(operations),
            "total_duration_ms": total_duration,
            "avg_duration_ms": avg_duration,
            "slow_operations": len(slow_ops),
            "recent_operations": [op.to_dict() for op in operations[-10:]]
        }
    
    def _generate_timeline(self, activity: AgentActivity) -> List[Dict[str, str]]:
        """Generate a timeline of key events"""
        timeline = []
        
        # Add phase transitions
        phase_ops = [
            op for op in activity.operations
            if "phase" in op.details
        ]
        
        for op in phase_ops:
            timeline.append({
                "time": op.timestamp.isoformat(),
                "event": f"Entered {op.details['phase']} phase",
                "type": "phase_change"
            })
        
        # Add significant operations
        significant_ops = [
            op for op in activity.operations
            if op.type in [OperationType.FILE_WRITE, OperationType.GIT_COMMIT, OperationType.ERROR]
        ]
        
        for op in significant_ops[:10]:  # Limit to 10 most recent
            timeline.append({
                "time": op.timestamp.isoformat(),
                "event": op.description,
                "type": op.type.value
            })
        
        # Sort by time
        timeline.sort(key=lambda x: x["time"])
        
        return timeline
    
    def _generate_recommendations(self, activity: AgentActivity) -> List[str]:
        """Generate recommendations based on activity analysis"""
        recommendations = []
        
        # Check success rate
        success_rate = activity._calculate_success_rate()
        if success_rate < 0.8:
            recommendations.append(
                f"Success rate is {success_rate:.1%}. Consider reviewing error patterns."
            )
        
        # Check for repeated errors
        error_types = defaultdict(int)
        for error in activity.errors:
            error_desc = error.get("description", "Unknown")
            error_types[error_desc] += 1
        
        for error_desc, count in error_types.items():
            if count > 2:
                recommendations.append(
                    f"Error '{error_desc}' occurred {count} times. Investigate root cause."
                )
        
        # Check phase duration
        duration = activity.get_duration()
        if activity.phase == Phase.PLANNING and duration > timedelta(minutes=10):
            recommendations.append(
                "Planning phase is taking longer than usual. Consider breaking down the task."
            )
        
        # Check file access patterns
        if len(activity.files_accessed) > 20:
            recommendations.append(
                f"Agent accessed {len(activity.files_accessed)} files. Consider focusing scope."
            )
        
        return recommendations
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system-wide overview of all agent activities"""
        active_agents = [
            agent_id for agent_id, activity in self.activities.items()
            if activity.phase not in [Phase.COMPLETING, Phase.FAILED]
        ]
        
        # Aggregate metrics
        total_operations = sum(len(a.operations) for a in self.activities.values())
        total_errors = sum(len(a.errors) for a in self.activities.values())
        
        # Recent operations across all agents
        all_operations = []
        for activity in self.activities.values():
            all_operations.extend(activity.operations)
        
        all_operations.sort(key=lambda x: x.timestamp, reverse=True)
        recent_ops = [op.to_dict() for op in all_operations[:20]]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_agents": len(active_agents),
            "total_agents": len(self.activities),
            "total_operations": total_operations,
            "total_errors": total_errors,
            "error_rate": total_errors / total_operations if total_operations > 0 else 0,
            "active_agent_ids": active_agents,
            "recent_operations": recent_ops,
            "metrics": dict(self.metrics)
        }
    
    def _update_metrics(self, operation: Operation):
        """Update system metrics"""
        # Count operations by type
        self.metrics[f"ops_{operation.type.value}"] += 1
        
        # Count operations by agent
        self.metrics[f"agent_{operation.agent_id}_ops"] += 1
        
        # Track errors
        if not operation.success:
            self.metrics["total_errors"] += 1
            self.metrics[f"agent_{operation.agent_id}_errors"] += 1
        
        # Track file operations
        if operation.type in [OperationType.FILE_READ, OperationType.FILE_WRITE]:
            self.metrics["file_operations"] += 1
    
    async def _log_to_file(self, operation: Operation):
        """Log operation to file"""
        try:
            # Create daily log file
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(
                self.config["log_directory"],
                f"agent_activity_{date_str}.jsonl"
            )
            
            # Append operation
            with open(log_file, "a") as f:
                f.write(json.dumps(operation.to_dict()) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to log to file: {e}")
    
    async def _send_realtime_update(self, operation: Operation):
        """Send real-time update to WebSocket clients"""
        if not self.websocket_clients:
            return
        
        message = json.dumps({
            "type": "operation",
            "data": operation.to_dict()
        })
        
        # Send to all connected clients
        disconnected = []
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except:
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.websocket_clients.remove(client)
    
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        async def handle_client(websocket, path):
            """Handle WebSocket client connection"""
            self.websocket_clients.append(websocket)
            logger.info(f"WebSocket client connected: {websocket.remote_address}")
            
            try:
                # Send initial state
                overview = self.get_system_overview()
                await websocket.send(json.dumps({
                    "type": "overview",
                    "data": overview
                }))
                
                # Keep connection alive
                await websocket.wait_closed()
                
            finally:
                self.websocket_clients.remove(websocket)
                logger.info(f"WebSocket client disconnected: {websocket.remote_address}")
        
        # Start server
        server = await websockets.serve(
            handle_client,
            "localhost",
            self.config["websocket_port"]
        )
        
        logger.info(f"WebSocket server started on port {self.config['websocket_port']}")
    
    async def _metrics_aggregator(self):
        """Background task to aggregate metrics"""
        while self.running:
            await asyncio.sleep(60)  # Every minute
            
            # Calculate aggregate metrics
            self.metrics["avg_operations_per_agent"] = (
                sum(len(a.operations) for a in self.activities.values()) /
                len(self.activities) if self.activities else 0
            )
    
    async def _log_cleaner(self):
        """Background task to clean old logs"""
        while self.running:
            await asyncio.sleep(3600)  # Every hour
            
            if not self.config["log_to_file"]:
                continue
            
            # Remove logs older than retention period
            retention_days = self.config["retention_days"]
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            try:
                for filename in os.listdir(self.config["log_directory"]):
                    if filename.startswith("agent_activity_") and filename.endswith(".jsonl"):
                        # Extract date from filename
                        date_str = filename.replace("agent_activity_", "").replace(".jsonl", "")
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        
                        if file_date < cutoff_date:
                            file_path = os.path.join(self.config["log_directory"], filename)
                            os.remove(file_path)
                            logger.info(f"Removed old log file: {filename}")
                            
            except Exception as e:
                logger.error(f"Error cleaning logs: {e}")
    
    async def _save_state(self):
        """Save current state to file"""
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "activities": {
                    agent_id: activity.get_summary()
                    for agent_id, activity in self.activities.items()
                },
                "metrics": dict(self.metrics)
            }
            
            state_file = os.path.join(
                self.config["log_directory"],
                "engine_state.json"
            )
            
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save state: {e}")


# Example usage
if __name__ == "__main__":
    async def main():
        # Create engine
        engine = ExplainabilityEngine()
        
        # Start engine
        await engine.start()
        
        # Simulate agent activity
        agent_id = "backend_agent"
        engine.start_agent_activity(agent_id, "TASK-001")
        
        # Log planning phase
        engine.update_agent_phase(agent_id, Phase.PLANNING)
        engine.log_decision(
            agent_id,
            decision="Use repository pattern",
            reasoning="Separates data access from business logic",
            options_considered=["Direct DB access", "Repository pattern", "Active Record"],
            confidence=0.9
        )
        
        # Log implementation phase
        engine.update_agent_phase(agent_id, Phase.IMPLEMENTING)
        
        # Log file operations
        engine.log_operation(
            agent_id,
            OperationType.FILE_WRITE,
            "Created user repository",
            {"file_path": "src/repositories/user_repository.py"},
            duration_ms=150
        )
        
        # Log code generation
        engine.log_operation(
            agent_id,
            OperationType.CODE_GENERATE,
            "Generated user model",
            {"lines": 45, "complexity": "medium"},
            duration_ms=300
        )
        
        # Log an error
        engine.log_operation(
            agent_id,
            OperationType.ERROR,
            "Import error in test file",
            {"error": "Module not found: user_repository"},
            success=False
        )
        
        # Get explanation
        explanation = engine.get_agent_explanation(agent_id)
        print(json.dumps(explanation, indent=2))
        
        # Get system overview
        overview = engine.get_system_overview()
        print(json.dumps(overview, indent=2))
        
        # Simulate some activity
        await asyncio.sleep(5)
        
        # Stop engine
        await engine.stop()
    
    # Run example
    asyncio.run(main())