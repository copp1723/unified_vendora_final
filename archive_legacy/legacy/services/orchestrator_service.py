"""
Orchestrator Service
Manages agent coordination, task distribution, and system orchestration
Python equivalent of the JavaScript orchestration system
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class Agent:
    """Agent data class"""
    id: str
    type: str
    status: AgentStatus
    current_task: Optional[str] = None
    branch: Optional[str] = None
    last_activity: Optional[datetime] = None


@dataclass
class Task:
    """Task data class"""
    id: str
    description: str
    agent_type: str
    priority: int = 1
    dependencies: List[str] = None
    status: str = "pending"
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class OrchestratorService:
    """
    Main orchestrator service that manages agent coordination and task distribution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.file_locks: Dict[str, str] = {}  # file_path -> agent_id
        self.running = False
        self._sync_interval = 300  # 5 minutes
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "base_branch": "main",
            "sync_interval": 300,
            "max_agents": 5,
            "quality_gates": {
                "lint": True,
                "tests": True,
                "security": True,
                "coverage": 80
            },
            "agent_types": {
                "frontend": {
                    "name": "Frontend Agent",
                    "capabilities": ["React", "TypeScript", "CSS"]
                },
                "backend": {
                    "name": "Backend Agent",
                    "capabilities": ["Node.js", "API", "Database"]
                },
                "database": {
                    "name": "Database Agent",
                    "capabilities": ["SQL", "Schema", "Migrations"]
                },
                "testing": {
                    "name": "Testing Agent",
                    "capabilities": ["Unit Tests", "Integration Tests", "E2E"]
                }
            }
        }
    
    async def start(self):
        """Start the orchestrator service"""
        logger.info("🚀 Starting Orchestrator Service")
        self.running = True
        
        # Initialize agents
        await self._initialize_agents()
        
        # Start background tasks
        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._monitor_loop())
        
        logger.info("✅ Orchestrator Service started successfully")
    
    async def stop(self):
        """Stop the orchestrator service"""
        logger.info("🛑 Stopping Orchestrator Service")
        self.running = False
        await self._cleanup()
        logger.info("✅ Orchestrator Service stopped")
    
    async def _initialize_agents(self):
        """Initialize all configured agents"""
        for agent_type, agent_config in self.config["agent_types"].items():
            agent = Agent(
                id=agent_type,
                type=agent_type,
                status=AgentStatus.IDLE
            )
            self.agents[agent_type] = agent
            logger.info(f"Initialized {agent_config['name']}")
    
    async def assign_task(self, task: Task) -> bool:
        """
        Assign a task to an appropriate agent
        
        Args:
            task: Task to assign
            
        Returns:
            bool: True if task was assigned successfully
        """
        # Find available agent
        agent = self._find_available_agent(task.agent_type)
        if not agent:
            logger.warning(f"No available agent for task {task.id}")
            return False
        
        # Check dependencies
        if not self._check_dependencies(task):
            logger.info(f"Task {task.id} has unmet dependencies")
            return False
        
        # Assign task
        agent.status = AgentStatus.WORKING
        agent.current_task = task.id
        agent.last_activity = datetime.now()
        
        # Create branch for agent
        branch_name = f"feature/{agent.type}/{task.id.lower()}"
        await self._create_branch(branch_name)
        agent.branch = branch_name
        
        task.status = "in_progress"
        self.tasks[task.id] = task
        
        logger.info(f"✅ Assigned task {task.id} to {agent.type} agent")
        return True
    
    def _find_available_agent(self, agent_type: str) -> Optional[Agent]:
        """Find an available agent of the specified type"""
        agent = self.agents.get(agent_type)
        if agent and agent.status == AgentStatus.IDLE:
            return agent
        return None
    
    def _check_dependencies(self, task: Task) -> bool:
        """Check if all task dependencies are met"""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != "completed":
                return False
        return True
    
    async def _create_branch(self, branch_name: str):
        """Create a git branch for the agent"""
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True,
                capture_output=True
            )
            logger.info(f"Created branch: {branch_name}")
        except subprocess.CalledProcessError:
            # Branch might already exist
            subprocess.run(
                ["git", "checkout", branch_name],
                check=True,
                capture_output=True
            )
    
    def acquire_file_lock(self, file_path: str, agent_id: str) -> bool:
        """
        Acquire a lock on a file for an agent
        
        Args:
            file_path: Path to the file
            agent_id: ID of the agent requesting the lock
            
        Returns:
            bool: True if lock was acquired
        """
        if file_path in self.file_locks:
            current_owner = self.file_locks[file_path]
            if current_owner != agent_id:
                logger.warning(f"File {file_path} is locked by {current_owner}")
                return False
        
        self.file_locks[file_path] = agent_id
        logger.debug(f"Agent {agent_id} acquired lock on {file_path}")
        return True
    
    def release_file_lock(self, file_path: str, agent_id: str):
        """Release a file lock"""
        if self.file_locks.get(file_path) == agent_id:
            del self.file_locks[file_path]
            logger.debug(f"Agent {agent_id} released lock on {file_path}")
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        return {
            "id": agent.id,
            "type": agent.type,
            "status": agent.status.value,
            "current_task": agent.current_task,
            "branch": agent.branch,
            "last_activity": agent.last_activity.isoformat() if agent.last_activity else None
        }
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        return {
            agent_id: self.get_agent_status(agent_id)
            for agent_id in self.agents
        }
    
    async def _sync_loop(self):
        """Background task to sync agent branches"""
        while self.running:
            await asyncio.sleep(self._sync_interval)
            await self._sync_all_agents()
    
    async def _sync_all_agents(self):
        """Sync all agent branches with base branch"""
        logger.info("🔄 Syncing all agent branches")
        
        for agent in self.agents.values():
            if agent.branch and agent.status == AgentStatus.WORKING:
                try:
                    # Save current branch
                    current_branch = subprocess.run(
                        ["git", "branch", "--show-current"],
                        capture_output=True,
                        text=True
                    ).stdout.strip()
                    
                    # Checkout agent branch and merge base
                    subprocess.run(["git", "checkout", agent.branch], check=True)
                    subprocess.run(
                        ["git", "merge", self.config["base_branch"], "--no-commit"],
                        check=False
                    )
                    
                    # Return to original branch
                    subprocess.run(["git", "checkout", current_branch], check=True)
                    
                    logger.info(f"✅ Synced {agent.type} agent branch")
                except Exception as e:
                    logger.error(f"❌ Failed to sync {agent.type}: {e}")
    
    async def _monitor_loop(self):
        """Background task to monitor agent health"""
        while self.running:
            await asyncio.sleep(60)  # Check every minute
            await self._check_agent_health()
    
    async def _check_agent_health(self):
        """Check health of all agents"""
        for agent in self.agents.values():
            if agent.status == AgentStatus.WORKING and agent.last_activity:
                # Check if agent has been inactive for too long
                inactive_time = (datetime.now() - agent.last_activity).seconds
                if inactive_time > 600:  # 10 minutes
                    logger.warning(f"⚠️ Agent {agent.type} appears stuck")
                    agent.status = AgentStatus.BLOCKED
    
    async def complete_task(self, agent_id: str, task_id: str, success: bool = True):
        """Mark a task as completed"""
        agent = self.agents.get(agent_id)
        task = self.tasks.get(task_id)
        
        if not agent or not task:
            return
        
        # Update task status
        task.status = "completed" if success else "failed"
        
        # Update agent status
        agent.status = AgentStatus.IDLE
        agent.current_task = None
        
        # Release all file locks held by this agent
        locks_to_release = [
            path for path, owner in self.file_locks.items()
            if owner == agent_id
        ]
        for path in locks_to_release:
            self.release_file_lock(path, agent_id)
        
        logger.info(f"✅ Task {task_id} completed by {agent_id}")
    
    async def _cleanup(self):
        """Cleanup resources"""
        # Release all file locks
        self.file_locks.clear()
        
        # Reset all agents to idle
        for agent in self.agents.values():
            agent.status = AgentStatus.IDLE
            agent.current_task = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        total_agents = len(self.agents)
        active_agents = sum(1 for a in self.agents.values() if a.status == AgentStatus.WORKING)
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == "completed")
        
        return {
            "agents": {
                "total": total_agents,
                "active": active_agents,
                "idle": total_agents - active_agents
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": sum(1 for t in self.tasks.values() if t.status == "in_progress"),
                "pending": sum(1 for t in self.tasks.values() if t.status == "pending")
            },
            "file_locks": len(self.file_locks),
            "uptime": datetime.now().isoformat()
        }


# Example usage
if __name__ == "__main__":
    async def main():
        # Create orchestrator
        orchestrator = OrchestratorService()
        
        # Start service
        await orchestrator.start()
        
        # Create a test task
        task = Task(
            id="TEST-001",
            description="Create user authentication module",
            agent_type="backend"
        )
        
        # Assign task
        await orchestrator.assign_task(task)
        
        # Get status
        print(json.dumps(orchestrator.get_all_agent_statuses(), indent=2))
        
        # Get metrics
        print(json.dumps(orchestrator.get_metrics(), indent=2))
        
        # Simulate some work
        await asyncio.sleep(5)
        
        # Complete task
        await orchestrator.complete_task("backend", "TEST-001")
        
        # Stop service
        await orchestrator.stop()
    
    # Run example
    asyncio.run(main())