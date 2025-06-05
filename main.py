from smolagents import CodeAgent, LiteLLMModel
from smolagents.tools import ToolCollection
import gradio as gr

additional_instructions = """
ADDITIONAL IMPORTANT INSTRUCTIONS:
use the tool "final_answer" in the code block to provide the answer to the user. 
Prints are only for debugging purposes. So, to give your results concatenate everything you want to print in a single "final_answer" call as such : final_answer(f"your answer here").

Example:
```python
result = tool_call(arg1, arg2, arg3)
final_answer(f"your answer here {result}") # here print statement has been replaced by final_answer tool call
```
"""

def run_agent(message, history):
    """Create a new MCP connection for each request to avoid event loop issues."""
    with ToolCollection.from_mcp(
            {"url": "https://notredameslab-nf-ontology.hf.space/gradio_api/mcp/sse", "transport": "sse"},
            trust_remote_code=True  # Acknowledge that we trust this remote MCP server
        ) as tool_collection:

        model = LiteLLMModel(
            model_id="ollama/devstral:latest",
            #model_id="ollama/qwen3:0.6b",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(
            tools=tool_collection.tools,
            model=model,
            additional_authorized_imports=["inspect", "json"]
        )

        
        return str(agent.run(message + " put the result in a final_answer call such as final_answer(f'your answer here')"))
        
if __name__ == "__main__":
    demo = gr.ChatInterface(
        fn=run_agent,
        type="messages",
        examples=["can you extract input/output metadata from fastqc nf-core module ?"],
        title="Agent with MCP Tools (Per-Request Connection)",
        description="This version creates a new MCP connection for each request."
    )

    demo.launch() 