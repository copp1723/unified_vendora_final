# VENDORA Unified Project

A unified codebase consolidating components from multiple VENDORA projects for building an AI-powered analytics platform.

## Project Structure

- **analytics/** - Core analytics modules (semantic layer, trend analysis, precision scoring)
- **insights/** - Insight generation and processing (digest system, feedback engine, insight flow)
- **services/** - Multi-agent orchestration services (orchestrator, multi-agent service, explainability engine)
- **agents/** - Specialized agents (email processing, conversation AI, data analysis)
- **src/** - Main application entry point
- **vendora_rep_src/** - React UI components and frontend code
- **db/** - Database schema definitions
- **utils/** - Utility functions (data normalization)

## Architecture

This project implements a hierarchical multi-agent system with three levels:
1. **Orchestrator** (Level 1) - Task ingestion and intelligent dispatch
2. **Specialist Agents** (Level 2) - Domain-specific analysis and insight generation
3. **Master Analyst** (Level 3) - Validation, synthesis, and quality control

Built for deployment on Google Cloud Platform using Gemini API.
