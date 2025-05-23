"""
FACT System Agentic Flow Orchestrator

This module provides intelligent flow control for multi-step reasoning,
ensuring the system completes complex queries that require multiple steps.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import structlog


logger = structlog.get_logger(__name__)


class FlowState(Enum):
    """Flow execution states."""
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    GATHERING_DATA = "gathering_data"
    PROCESSING = "processing"
    COMPLETING = "completing"
    FINISHED = "finished"
    ERROR = "error"


class AgenticStep:
    """Represents a single step in the agentic flow."""
    
    def __init__(self, step_type: str, description: str, required_tools: List[str] = None):
        self.step_type = step_type
        self.description = description
        self.required_tools = required_tools or []
        self.completed = False
        self.result = None
        self.error = None
        self.timestamp = time.time()
    
    def mark_completed(self, result: Any) -> None:
        """Mark step as completed with result."""
        self.completed = True
        self.result = result
        self.timestamp = time.time()
    
    def mark_failed(self, error: str) -> None:
        """Mark step as failed with error."""
        self.error = error
        self.timestamp = time.time()


class AgenticFlowOrchestrator:
    """Orchestrates multi-step agentic flows for complex queries."""
    
    def __init__(self, driver):
        """Initialize flow orchestrator with driver reference."""
        self.driver = driver
        self.current_flow: Optional[str] = None
        self.flow_state = FlowState.INITIALIZING
        self.steps: List[AgenticStep] = []
        self.max_steps = 10
        self.step_timeout = 30.0
        self._recursion_depth = 0
        self._max_recursion_depth = 3
    
    def analyze_query_complexity(self, user_input: str) -> Tuple[bool, List[str]]:
        """
        Analyze if query requires multi-step processing.
        
        Args:
            user_input: User's query
            
        Returns:
            Tuple of (is_complex, required_steps)
        """
        user_lower = user_input.lower()
        
        # Patterns that indicate complex multi-step queries
        complex_patterns = {
            "comparison": ["compare", "versus", "vs", "difference between", "contrast"],
            "trend_analysis": ["trend", "over time", "change", "growth", "decline"],
            "aggregation": ["total", "average", "sum", "count", "all companies"],
            "multi_table": ["revenue trends", "company performance", "financial analysis"],
            "conditional": ["if", "when", "where", "companies in", "sector"]
        }
        
        required_steps = []
        is_complex = False
        
        for step_type, patterns in complex_patterns.items():
            if any(pattern in user_lower for pattern in patterns):
                required_steps.append(step_type)
                is_complex = True
        
        # Always require schema check for database queries
        if any(word in user_lower for word in ["company", "companies", "revenue", "financial", "data"]):
            if "schema_check" not in required_steps:
                required_steps.insert(0, "schema_check")
        
        logger.info("Query complexity analysis", 
                   is_complex=is_complex, 
                   required_steps=required_steps)
        
        return is_complex, required_steps
    
    def create_execution_plan(self, user_input: str, required_steps: List[str]) -> List[AgenticStep]:
        """
        Create detailed execution plan for complex query.
        
        Args:
            user_input: User's query
            required_steps: Required step types
            
        Returns:
            List of execution steps
        """
        steps = []
        
        # Step 1: Schema check (if needed)
        if "schema_check" in required_steps:
            steps.append(AgenticStep(
                "schema_check",
                "Get database schema to understand available tables and columns",
                ["SQL.GetSchema"]
            ))
        
        # Step 2: Data gathering based on query type
        if "comparison" in required_steps:
            steps.append(AgenticStep(
                "data_gathering",
                "Query data for all entities to be compared",
                ["SQL.QueryReadonly"]
            ))
        elif "trend_analysis" in required_steps:
            steps.append(AgenticStep(
                "trend_data",
                "Query historical data for trend analysis",
                ["SQL.QueryReadonly"]
            ))
        elif "aggregation" in required_steps:
            steps.append(AgenticStep(
                "aggregate_data",
                "Query and aggregate data across entities",
                ["SQL.QueryReadonly"]
            ))
        else:
            steps.append(AgenticStep(
                "data_query",
                "Query specific data requested by user",
                ["SQL.QueryReadonly"]
            ))
        
        # Step 3: Analysis and formatting
        steps.append(AgenticStep(
            "analysis",
            "Analyze data and format response for user",
            []
        ))
        
        logger.info("Created execution plan", step_count=len(steps))
        return steps
    
    async def execute_flow(self, user_input: str) -> str:
        """
        Execute agentic flow for complex query.
        
        Args:
            user_input: User's query
            
        Returns:
            Complete response
        """
        try:
            # Check recursion depth to prevent infinite loops
            self._recursion_depth += 1
            if self._recursion_depth > self._max_recursion_depth:
                logger.warning("Maximum recursion depth reached, falling back to simple processing")
                self._recursion_depth -= 1
                return "I'll provide a direct answer to your query without complex analysis."
            
            # Analyze query complexity
            is_complex, required_steps = self.analyze_query_complexity(user_input)
            
            if not is_complex:
                # Simple query, use standard processing but avoid recursion
                self._recursion_depth -= 1
                return await self._simple_query_processing(user_input)
            
            # Complex query, use orchestrated flow
            self.flow_state = FlowState.ANALYZING
            self.steps = self.create_execution_plan(user_input, required_steps)
            
            # Execute steps
            accumulated_context = []
            
            for i, step in enumerate(self.steps):
                logger.info("Executing step", 
                           step_number=i+1, 
                           total_steps=len(self.steps),
                           step_type=step.step_type)
                
                self.flow_state = FlowState.GATHERING_DATA
                
                try:
                    # Create step-specific prompt
                    step_prompt = self._create_step_prompt(step, user_input, accumulated_context)
                    
                    # Execute step using simple processing to avoid recursion
                    step_result = await self._simple_query_processing(step_prompt)
                    
                    step.mark_completed(step_result)
                    accumulated_context.append({
                        "step": step.step_type,
                        "result": step_result
                    })
                    
                    logger.info("Step completed successfully", step_type=step.step_type)
                    
                except Exception as e:
                    step.mark_failed(str(e))
                    logger.error("Step failed", step_type=step.step_type, error=str(e))
                    
                    # Try to continue with remaining steps
                    continue
            
            # Generate final response
            self.flow_state = FlowState.COMPLETING
            final_response = await self._generate_final_response(user_input, accumulated_context)
            
            self.flow_state = FlowState.FINISHED
            self._recursion_depth -= 1
            return final_response
            
        except Exception as e:
            self.flow_state = FlowState.ERROR
            logger.error("Agentic flow failed", error=str(e))
            self._recursion_depth -= 1
            return f"I encountered an error while processing your complex query: {str(e)}"
    
    def _create_step_prompt(self, step: AgenticStep, original_query: str, context: List[Dict]) -> str:
        """Create a prompt for executing a specific step."""
        base_prompt = f"Original user query: {original_query}\n\n"
        
        if context:
            base_prompt += "Previous step results:\n"
            for ctx in context:
                base_prompt += f"- {ctx['step']}: {ctx['result'][:200]}...\n"
            base_prompt += "\n"
        
        if step.step_type == "schema_check":
            return base_prompt + "First, get the database schema to understand what tables and columns are available for this query."
        
        elif step.step_type == "data_gathering":
            return base_prompt + "Now query the specific data needed to answer the user's question. Use the schema information from the previous step."
        
        elif step.step_type == "trend_data":
            return base_prompt + "Query historical data to analyze trends over time. Include time-based columns in your query."
        
        elif step.step_type == "aggregate_data":
            return base_prompt + "Query and aggregate the data to get totals, averages, or counts as requested by the user."
        
        elif step.step_type == "analysis":
            return base_prompt + "Based on all the data gathered in previous steps, provide a comprehensive answer to the user's original question. Include specific numbers, comparisons, and insights."
        
        else:
            return base_prompt + f"Execute the {step.step_type} step: {step.description}"
    
    async def _generate_final_response(self, original_query: str, context: List[Dict]) -> str:
        """Generate final comprehensive response."""
        if not context:
            return "I was unable to gather the necessary data to answer your question."
        
        # Create comprehensive prompt for final response
        final_prompt = f"""Original question: {original_query}

Here's all the data I gathered:
"""
        
        for i, ctx in enumerate(context, 1):
            final_prompt += f"\nStep {i} ({ctx['step']}):\n{ctx['result']}\n"
        
        final_prompt += "\nNow provide a comprehensive, well-structured answer to the original question using all this data. Include specific numbers, trends, and insights."
        
        try:
            final_response = await self.driver.process_query(final_prompt)
            return final_response
        except Exception as e:
            # Fallback: format the data ourselves
            logger.warning("Final response generation failed, using fallback formatting")
            return self._format_fallback_response(original_query, context)
    
    def _format_fallback_response(self, original_query: str, context: List[Dict]) -> str:
        """Format a fallback response if final generation fails."""
        response = f"Here's what I found regarding: {original_query}\n\n"
        
        for i, ctx in enumerate(context, 1):
            response += f"Step {i}: {ctx['result']}\n\n"
        
        return response
    
    def get_flow_status(self) -> Dict[str, Any]:
        """Get current flow execution status."""
        return {
            "state": self.flow_state.value,
            "total_steps": len(self.steps),
            "completed_steps": sum(1 for step in self.steps if step.completed),
            "current_step": next((i for i, step in enumerate(self.steps) if not step.completed), None),
            "errors": [step.error for step in self.steps if step.error]
        }
    
    async def _simple_query_processing(self, user_input: str) -> str:
        """Process simple queries without complex orchestration to avoid recursion."""
        try:
            # Use driver's process_query with agentic flow disabled to avoid recursion
            return await self.driver.process_query(user_input, use_agentic_flow=False)
            
        except Exception as e:
            logger.error("Simple query processing failed", error=str(e))
            return "I encountered an error processing your query."
