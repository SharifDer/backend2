"""
Simplified Geospatial Analysis Agent - Pure MCP Orchestration with Memory

This agent focuses solely on tool orchestration via MCP protocol with conversation memory.
All report generation, file saving, and visualization handling is done by the server tools.
"""

import asyncio
import uuid
import os
import json
from typing import Optional, Dict, Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from system_prompts import TERRITORY_OPTIMIZATION_PROMPT
from config import Config



class AnalysisOutput(BaseModel):
    """Structured output for analysis with file handles and data files."""
    
    report_file: str = Field(description="Path to the generated markdown report file")
    data_files: Optional[Dict[str, str]] = Field(description="Dictionary of data files for downstream processing", default_factory=dict)
    response: str = Field(description="Human-readable response to be shown in chat box")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata about the analysis", default_factory=dict)


class SimpleMCPClient:
    """
    Simple MCP client that orchestrates tools without duplicating their functionality.
    All report generation is handled by server tools.
    """
    
    def __init__(self, 
                 session_id: str = None,
                 config_override: dict = None,
                 model: str = None,
                 temperature: float = None):
        """
        Initialize the MCP client with memory support
        
        Args:
            session_id: Session identifier for conversation continuity
            config_override: Optional configuration overrides
            model: OpenAI model to use (defaults to config)
            temperature: Model temperature setting (defaults to config)
        """
        print("🚀 Initializing Simple MCP Client with Memory...")
        
        # Session management
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.default_thread_id = f"conversation_{self.session_id}"
        
        # Validate configuration
        if not Config.validate_paths():
            raise ValueError("Required paths are missing. Please check configuration.")
        
        # Set model parameters
        self.model = model or Config.DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else Config.DEFAULT_TEMPERATURE
        
        # Get MCP configuration
        self.mcp_config = Config.get_mcp_config()
        
        # Apply any configuration overrides
        if config_override:
            self.mcp_config.update(config_override)
        
        # Initialize memory checkpointer
        self.checkpointer = MemorySaver()
        
        # Initialize client and agent (will be set up in connect method)
        self.client = None
        self.agent = None
        self.tools = None
        self.secrets = None
        
        # Initialize Pydantic output parser
        self.parser = PydanticOutputParser(pydantic_object=AnalysisOutput)
        
        print(f"📋 Session ID: {self.session_id}")
        
    async def connect(self):
        """Connect to MCP server and initialize tools with memory"""
        print("🔌 Connecting to MCP server...")
        
        # Initialize MCP client
        self.client = MultiServerMCPClient(self.mcp_config)
        
        # Get available tools from the MCP server
        self.tools = await self.client.get_tools()
        print(f"📋 Available tools: {[tool.name for tool in self.tools]}")
        
        # Load API keys from secrets file (cache for reuse)
        if not self.secrets:
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'secrets', 'secrets_llm.json')
            with open(secrets_path, 'r') as f:
                self.secrets = json.load(f)
            print(f"🔑 Loaded Gemini API key: {self.secrets['gemini_api_key'][:20]}...{self.secrets['gemini_api_key'][-4:]}")
        
        # Create fresh LLM instance to avoid event loop issues
        llm = ChatGoogleGenerativeAI(
            model=self.model, 
            temperature=self.temperature,
            google_api_key=self.secrets['gemini_api_key']
        )
        
        # Create fresh agent with preserved checkpointer (maintains conversation memory)
        self.agent = create_react_agent(
            llm, 
            self.tools, 
            checkpointer=self.checkpointer
        )
        
        print("✅ MCP client successfully connected with memory!")
    
    def _refresh_agent(self):
        """Refresh the agent with a new LLM instance to avoid event loop issues while preserving memory"""
        if not self.tools or not self.secrets:
            raise ValueError("MCP client must be connected first. Call connect() method.")
        
        # Create fresh LLM instance
        llm = ChatGoogleGenerativeAI(
            model=self.model, 
            temperature=self.temperature,
            google_api_key=self.secrets['gemini_api_key']
        )
        
        # Create fresh agent with same checkpointer (preserves conversation memory)
        self.agent = create_react_agent(
            llm, 
            self.tools, 
            checkpointer=self.checkpointer
        )
        
    async def analyze_territories(self, user_query: str, thread_id: str = None) -> str:
        """
        Analyze territories based on user query with conversation memory.
        Pure tool orchestration - no file operations.
        
        Args:
            user_query: User's request for territory analysis
            thread_id: Thread identifier for conversation continuity (optional)
        
        Returns:
            Final response from the agent
        """
        if not self.tools or not self.secrets:
            raise ValueError("Agent not connected. Please call connect() first.")
        
        # Refresh agent to avoid event loop issues while preserving memory
        self._refresh_agent()
        
        # Use provided thread_id or default
        current_thread_id = thread_id or self.default_thread_id
        
        # Create configuration with thread_id for memory
        config = {"configurable": {"thread_id": current_thread_id}}
        
        # Create messages for the LLM
        messages = [
            SystemMessage(content=TERRITORY_OPTIMIZATION_PROMPT),
            HumanMessage(content=user_query)
        ]
        
        print(f"🔄 Processing query: {user_query[:100]}...")
        print(f"🧠 Using thread: {current_thread_id}")
        print(f"🤖 Using {self.model} with temperature {self.temperature}")
        
        # Let the LLM orchestrate tools via MCP with memory
        response = await self.agent.ainvoke({"messages": messages}, config=config)
        
        # Extract the final AI response
        return self._extract_final_response(response)
    
    async def analyze_territories_with_file_handle(self, user_query: str, thread_id: str = None) -> dict:
        """
        Analyze territories and return structured output for Dash app
        
        Args:
            user_query: User's request for territory analysis
            thread_id: Thread identifier for conversation continuity (optional)
        
        Returns:
            Dictionary with 'response' and 'structured_output' keys
        """
        if not self.tools or not self.secrets:
            raise ValueError("Agent not connected. Please call connect() first.")
        
        # Refresh agent to avoid event loop issues while preserving memory
        self._refresh_agent()
        
        # Use provided thread_id or default
        current_thread_id = thread_id or self.default_thread_id
        
        # Create configuration with thread_id for memory
        config = {"configurable": {"thread_id": current_thread_id}}
        
        # Get parser format instructions
        parser_instructions = self.parser.get_format_instructions()
        
        # Create enhanced system prompt with parser instructions
        enhanced_system_prompt = f"""{TERRITORY_OPTIMIZATION_PROMPT}

IMPORTANT: You must respond with a valid JSON object in the exact format specified below. 
{parser_instructions}

Make sure to include:
- report_file: The actual file path to the generated report
- data_files: Dictionary of any data files created for downstream processing
- response: A clear, human-readable summary of what was accomplished
- metadata: Any additional relevant information about the analysis"""
        
        # Create messages for the LLM
        messages = [
            SystemMessage(content=enhanced_system_prompt),
            HumanMessage(content=user_query)
        ]
        
        print(f"🔄 Processing query: {user_query[:100]}...")
        print(f"🧠 Using thread: {current_thread_id}")
        print(f"🤖 Using {self.model} with temperature {self.temperature}")
        
        # Let the LLM orchestrate tools via MCP with memory
        response = await self.agent.ainvoke({"messages": messages}, config=config)
        
        # Extract the final AI response
        raw_response = self._extract_final_response(response)
        
        # Debug print to check response type
        print(f"[DEBUG] Response type: {type(raw_response)}")
        print(f"[DEBUG] Response is dict: {isinstance(raw_response, dict)}")
        
        try:
            # Parse the structured output
            structured_output = self.parser.parse(raw_response)
            
            print(f"✅ Successfully parsed structured output")
            print(f"📄 Report file: {structured_output.report_file}")
            print(f"📊 Data files: {list(structured_output.data_files.keys()) if structured_output.data_files else 'None'}")
            
            # Return both legacy format for compatibility and structured output
            return {
                'response': structured_output.response,
                'raw_content': raw_response,  # Keep for backward compatibility
                'structured_output': structured_output
            }
            
        except Exception as e:
            print(f"⚠️ Failed to parse structured output: {e}")
            print(f"🔄 Falling back to legacy parsing")
            
            # Fallback to legacy format
            return {
                'response': raw_response,
                'raw_content': raw_response,
                'structured_output': None
            }
    
    def _extract_final_response(self, response) -> str:
        """Extract the final AI response from the agent output"""
        if isinstance(response, dict) and 'messages' in response:
            messages = response['messages']
            
            # Look for the last AI message with content
            for message in reversed(messages):
                if hasattr(message, '__class__') and 'AI' in str(message.__class__):
                    if hasattr(message, 'content') and message.content and message.content.strip():
                        return message.content
            
            return "✅ Territory analysis completed! Reports have been generated and saved by the system."
        else:
            return "✅ Analysis completed successfully."
    
    def _extract_file_handle_from_response(self, response) -> str:
        """
        Extract file handle from response for Dash app integration
        Returns the response with file handle information for parsing
        """
        if isinstance(response, dict) and 'messages' in response:
            messages = response['messages']
            
            # Look for the last AI message with content
            for message in reversed(messages):
                if hasattr(message, '__class__') and 'AI' in str(message.__class__):
                    if hasattr(message, 'content') and message.content and message.content.strip():
                        # Return the full content for file handle parsing
                        return message.content
        
        return response
    
    def get_conversation_history(self, thread_id: str = None) -> dict:
        """Get conversation history for a specific thread"""
        current_thread_id = thread_id or self.default_thread_id
        config = {"configurable": {"thread_id": current_thread_id}}
        
        try:
            # Get state from checkpointer
            state = self.checkpointer.get(config)
            if state and 'messages' in state:
                return {
                    "thread_id": current_thread_id,
                    "message_count": len(state['messages']),
                    "messages": state['messages']
                }
        except Exception as e:
            print(f"⚠️ Could not retrieve conversation history: {e}")
        
        return {"thread_id": current_thread_id, "message_count": 0, "messages": []}
    
    async def interactive_mode(self):
        """Run the agent in interactive mode with memory - simple conversation interface"""
        if not self.agent:
            print("❌ Agent not connected. Please call connect() first.")
            return
        
        print("\n" + "="*80)
        print("🎯 GEOSPATIAL ANALYSIS AGENT - Interactive Mode with Memory")
        print("="*80)
        print("💡 Ask me to analyze sales territories, optimize locations, or generate reports!")
        print("💡 I'll remember our conversation context automatically!")
        print("💡 Example: 'Create 6 sales territories for supermarkets in Riyadh'")
        print("💡 Type 'exit' to quit")
        print(f"🧠 Session: {self.session_id}")
        print("="*80)
        
        while True:
            try:
                # Get user input
                print(f"\n🎯 Enter your analysis request:")
                user_input = input(">>> ").strip()
                
                # Handle exit commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    print("⚠️ Please enter a query.")
                    continue
                
                # Process the query with memory
                print(f"\n🔄 Processing your request...")
                response = await self.analyze_territories(user_input)
                
                # Display results
                print(f"\n" + "="*80)
                print(f"📋 ANALYSIS COMPLETED")
                print("="*80)
                print(response)
                print("="*80)
                
                # Simple status message
                print(f"\n📁 All reports and visualizations have been automatically saved by the system.")
                print(f"📊 Check the server's reports directory for generated files.")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("🔄 Please try again with a different query.")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.close()


async def main():
    """Main entry point for the simplified MCP client"""
    try:
        # Create and run the client
        async with SimpleMCPClient() as client:
            await client.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())