"""
Multi-Agent Service
Manages multiple AI agents, their communication, and task execution
Python equivalent of the JavaScript multi-agent system
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import hashlib
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types for agent communication"""
    TASK_ASSIGNED = "task:assigned"
    TASK_COMPLETED = "task:completed"
    TASK_FAILED = "task:failed"
    STATUS_UPDATE = "status:update"
    HELP_REQUEST = "help:request"
    SYNC_REQUEST = "sync:request"
    CODE_REVIEW = "code:review"


@dataclass
class Message:
    """Message for inter-agent communication"""
    id: str
    from_agent: str
    to_agent: str
    type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.id:
            # Generate unique message ID
            content = f"{self.from_agent}{self.to_agent}{self.timestamp}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:8]


class BaseAgent(ABC):
    """
    Base class for all AI agents
    Provides common functionality and interface
    """
    
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.id = agent_id
        self.type = agent_type
        self.capabilities = capabilities
        self.status = "idle"
        self.current_task = None
        self.message_queue: List[Message] = []
        self.memory: Dict[str, Any] = {}
        self.senior_mode = False
        
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def validate_code(self, code: str, file_path: str) -> Dict[str, Any]:
        """Validate generated code"""
        pass
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming message"""
        logger.info(f"Agent {self.id} received message: {message.type.value}")
        
        if message.type == MessageType.TASK_ASSIGNED:
            return await self._handle_task_assignment(message)
        elif message.type == MessageType.HELP_REQUEST:
            return await self._handle_help_request(message)
        elif message.type == MessageType.CODE_REVIEW:
            return await self._handle_code_review(message)
        
        return None
    
    async def _handle_task_assignment(self, message: Message) -> Message:
        """Handle task assignment"""
        task = message.payload
        self.current_task = task
        self.status = "working"
        
        # Execute task
        result = await self.execute_task(task)
        
        # Return completion message
        return Message(
            id="",
            from_agent=self.id,
            to_agent=message.from_agent,
            type=MessageType.TASK_COMPLETED if result["success"] else MessageType.TASK_FAILED,
            payload=result
        )
    
    async def _handle_help_request(self, message: Message) -> Message:
        """Handle help request from another agent"""
        # Analyze the request
        help_type = message.payload.get("type", "general")
        context = message.payload.get("context", {})
        
        # Provide assistance based on capabilities
        assistance = await self._provide_assistance(help_type, context)
        
        return Message(
            id="",
            from_agent=self.id,
            to_agent=message.from_agent,
            type=MessageType.STATUS_UPDATE,
            payload={"assistance": assistance}
        )
    
    async def _handle_code_review(self, message: Message) -> Message:
        """Handle code review request"""
        code = message.payload.get("code", "")
        file_path = message.payload.get("file_path", "")
        
        review_result = await self.validate_code(code, file_path)
        
        return Message(
            id="",
            from_agent=self.id,
            to_agent=message.from_agent,
            type=MessageType.STATUS_UPDATE,
            payload={"review": review_result}
        )
    
    async def _provide_assistance(self, help_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide assistance to another agent"""
        # Default implementation - override in specialized agents
        return {
            "type": help_type,
            "suggestions": ["Consider breaking down the problem", "Check similar patterns in codebase"],
            "relevant_capabilities": [cap for cap in self.capabilities if help_type.lower() in cap.lower()]
        }
    
    def add_to_memory(self, key: str, value: Any):
        """Add information to agent's memory"""
        self.memory[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "task": self.current_task
        }
    
    def get_from_memory(self, key: str) -> Optional[Any]:
        """Retrieve information from memory"""
        mem_item = self.memory.get(key)
        return mem_item["value"] if mem_item else None


class StandardAgent(BaseAgent):
    """Standard AI agent implementation"""
    
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        super().__init__(agent_id, agent_type, capabilities)
        self.quality_threshold = 0.7
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with standard agent capabilities"""
        logger.info(f"StandardAgent {self.id} executing task: {task.get('id')}")
        
        try:
            # Simulate task analysis
            analysis = await self._analyze_task(task)
            
            # Generate implementation plan
            plan = await self._generate_plan(analysis)
            
            # Generate code
            code_files = []
            for file_spec in plan["files"]:
                code = await self._generate_code(file_spec, task)
                
                # Validate code
                validation = await self.validate_code(code, file_spec["path"])
                
                if validation["passed"]:
                    code_files.append({
                        "path": file_spec["path"],
                        "content": code,
                        "validation": validation
                    })
                else:
                    logger.warning(f"Code validation failed for {file_spec['path']}")
            
            # Store in memory
            self.add_to_memory(f"task_{task['id']}_files", code_files)
            
            return {
                "success": True,
                "task_id": task["id"],
                "files_created": len(code_files),
                "plan": plan,
                "files": code_files
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "task_id": task["id"],
                "error": str(e)
            }
    
    async def _analyze_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task requirements"""
        return {
            "complexity": "medium",
            "estimated_time": 300,  # seconds
            "required_files": 2,
            "dependencies": []
        }
    
    async def _generate_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate implementation plan"""
        return {
            "approach": "standard",
            "files": [
                {"path": "src/module.py", "type": "implementation"},
                {"path": "tests/test_module.py", "type": "test"}
            ],
            "steps": ["analyze", "implement", "test", "validate"]
        }
    
    async def _generate_code(self, file_spec: Dict[str, Any], task: Dict[str, Any]) -> str:
        """Generate code for a file"""
        # Simulate code generation
        if file_spec["type"] == "implementation":
            return f"""# {task['description']}
# Generated by {self.id}

class Module:
    def __init__(self):
        self.name = "{task['id']}"
    
    def execute(self):
        return "Task completed"
"""
        else:  # test
            return f"""# Tests for {task['id']}
import unittest
from src.module import Module

class TestModule(unittest.TestCase):
    def test_execute(self):
        module = Module()
        result = module.execute()
        self.assertEqual(result, "Task completed")
"""
    
    async def validate_code(self, code: str, file_path: str) -> Dict[str, Any]:
        """Validate generated code"""
        issues = []
        
        # Basic validation checks
        if len(code) < 10:
            issues.append("Code too short")
        
        if "TODO" in code:
            issues.append("Contains TODO comments")
        
        if not code.strip():
            issues.append("Empty code")
        
        # Check for basic patterns
        has_class = "class " in code
        has_function = "def " in code
        has_imports = "import " in code or "from " in code
        
        quality_score = sum([has_class, has_function, has_imports]) / 3
        
        return {
            "passed": len(issues) == 0 and quality_score >= self.quality_threshold,
            "issues": issues,
            "quality_score": quality_score,
            "metrics": {
                "lines": len(code.splitlines()),
                "has_class": has_class,
                "has_function": has_function,
                "has_imports": has_imports
            }
        }


class SeniorAgent(StandardAgent):
    """Senior AI agent with advanced capabilities"""
    
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        super().__init__(agent_id, agent_type, capabilities)
        self.senior_mode = True
        self.quality_threshold = 0.9
        self.patterns_library = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load advanced patterns library"""
        return {
            "design_patterns": ["Factory", "Observer", "Strategy", "Decorator"],
            "architectural_patterns": ["MVC", "Repository", "CQRS", "Event-Driven"],
            "best_practices": ["SOLID", "DRY", "KISS", "YAGNI"],
            "security": ["Input Validation", "Authentication", "Authorization", "Encryption"]
        }
    
    async def _generate_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate senior-level implementation plan"""
        plan = await super()._generate_plan(analysis)
        
        # Enhance with senior patterns
        plan["patterns"] = ["Repository Pattern", "Dependency Injection"]
        plan["quality_targets"] = {
            "test_coverage": 90,
            "code_complexity": "low",
            "documentation": "comprehensive"
        }
        
        return plan
    
    async def validate_code(self, code: str, file_path: str) -> Dict[str, Any]:
        """Enhanced validation for senior-level code"""
        # Start with standard validation
        validation = await super().validate_code(code, file_path)
        
        # Add senior-level checks
        senior_checks = {
            "has_docstrings": '"""' in code or "'''" in code,
            "has_type_hints": "->" in code or ": " in code,
            "follows_patterns": any(pattern in code for pattern in ["class", "def", "async"]),
            "has_error_handling": "try:" in code or "except" in code
        }
        
        validation["senior_checks"] = senior_checks
        validation["senior_score"] = sum(senior_checks.values()) / len(senior_checks)
        
        # Update passed status with senior requirements
        validation["passed"] = validation["passed"] and validation["senior_score"] >= 0.75
        
        return validation


class MultiAgentService:
    """
    Service to manage multiple AI agents and their interactions
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_bus: List[Message] = []
        self.communication_handlers: Dict[str, Callable] = {}
        self.running = False
        
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the service"""
        self.agents[agent.id] = agent
        logger.info(f"Registered agent: {agent.id} ({agent.type})")
    
    def create_standard_agents(self):
        """Create standard set of agents"""
        agent_configs = [
            ("frontend", ["React", "TypeScript", "CSS", "HTML"]),
            ("backend", ["Python", "Node.js", "API", "Database"]),
            ("database", ["SQL", "Schema Design", "Migrations", "Optimization"]),
            ("testing", ["Unit Tests", "Integration Tests", "E2E", "TDD"]),
            ("devops", ["CI/CD", "Docker", "Kubernetes", "Monitoring"])
        ]
        
        for agent_type, capabilities in agent_configs:
            agent = StandardAgent(
                agent_id=f"{agent_type}_agent",
                agent_type=agent_type,
                capabilities=capabilities
            )
            self.register_agent(agent)
    
    def create_senior_agents(self):
        """Create senior-level agents"""
        agent_configs = [
            ("architect", ["System Design", "Architecture Patterns", "Scalability", "Security"]),
            ("lead", ["Code Review", "Best Practices", "Mentoring", "Standards"])
        ]
        
        for agent_type, capabilities in agent_configs:
            agent = SeniorAgent(
                agent_id=f"senior_{agent_type}_agent",
                agent_type=agent_type,
                capabilities=capabilities
            )
            self.register_agent(agent)
    
    async def send_message(self, message: Message):
        """Send a message through the communication bus"""
        self.message_bus.append(message)
        
        # Process immediately if recipient is available
        recipient = self.agents.get(message.to_agent)
        if recipient:
            response = await recipient.process_message(message)
            if response:
                self.message_bus.append(response)
    
    async def broadcast_message(self, from_agent: str, msg_type: MessageType, payload: Dict[str, Any]):
        """Broadcast a message to all agents"""
        for agent_id in self.agents:
            if agent_id != from_agent:
                message = Message(
                    id="",
                    from_agent=from_agent,
                    to_agent=agent_id,
                    type=msg_type,
                    payload=payload
                )
                await self.send_message(message)
    
    async def assign_task(self, task: Dict[str, Any], agent_id: str) -> bool:
        """Assign a task to a specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        # Send task assignment message
        message = Message(
            id="",
            from_agent="orchestrator",
            to_agent=agent_id,
            type=MessageType.TASK_ASSIGNED,
            payload=task
        )
        
        await self.send_message(message)
        return True
    
    async def request_collaboration(self, requesting_agent: str, helping_agent: str, context: Dict[str, Any]):
        """Request collaboration between agents"""
        message = Message(
            id="",
            from_agent=requesting_agent,
            to_agent=helping_agent,
            type=MessageType.HELP_REQUEST,
            payload=context
        )
        
        await self.send_message(message)
    
    def get_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        return {
            agent_id: {
                "id": agent.id,
                "type": agent.type,
                "status": agent.status,
                "current_task": agent.current_task,
                "capabilities": agent.capabilities,
                "senior_mode": agent.senior_mode
            }
            for agent_id, agent in self.agents.items()
        }
    
    def get_communication_metrics(self) -> Dict[str, Any]:
        """Get communication metrics"""
        message_types = {}
        for msg in self.message_bus:
            msg_type = msg.type.value
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        return {
            "total_messages": len(self.message_bus),
            "message_types": message_types,
            "active_agents": sum(1 for a in self.agents.values() if a.status == "working"),
            "total_agents": len(self.agents)
        }
    
    async def start(self):
        """Start the multi-agent service"""
        logger.info("🚀 Starting Multi-Agent Service")
        self.running = True
        
        # Create standard agents
        self.create_standard_agents()
        self.create_senior_agents()
        
        logger.info(f"✅ Started with {len(self.agents)} agents")
    
    async def stop(self):
        """Stop the multi-agent service"""
        logger.info("🛑 Stopping Multi-Agent Service")
        self.running = False
        
        # Clear message bus
        self.message_bus.clear()
        
        logger.info("✅ Multi-Agent Service stopped")


# Example usage
if __name__ == "__main__":
    async def main():
        # Create service
        service = MultiAgentService()
        
        # Start service
        await service.start()
        
        # Create a test task
        task = {
            "id": "TASK-001",
            "description": "Create user authentication module",
            "requirements": ["JWT tokens", "Password hashing", "Session management"]
        }
        
        # Assign to backend agent
        await service.assign_task(task, "backend_agent")
        
        # Request collaboration
        await service.request_collaboration(
            "backend_agent",
            "senior_architect_agent",
            {"type": "architecture_review", "context": task}
        )
        
        # Get status
        print(json.dumps(service.get_agent_statuses(), indent=2))
        
        # Get metrics
        print(json.dumps(service.get_communication_metrics(), indent=2))
        
        # Simulate some work
        await asyncio.sleep(2)
        
        # Stop service
        await service.stop()
    
    # Run example
    asyncio.run(main())