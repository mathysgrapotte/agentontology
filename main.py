from smolagents import CodeAgent, LiteLLMModel
from smolagents.tools import ToolCollection
import gradio as gr

def chat_with_agent(message, history):
    """Initialize MCP client for each request to avoid connection issues"""
    try:
        with ToolCollection.from_mcp(
            {"url": "https://notredameslab-nf-ontology.hf.space/gradio_api/mcp/sse", "transport": "sse"},
            trust_remote_code=True  # Acknowledge that we trust this remote MCP server
        ) as tool_collection:
            
            model = LiteLLMModel(
                model_id="ollama/devstral:latest",
                api_base="http://localhost:11434",
            )

            agent = CodeAgent(
                tools=tool_collection.tools,
                model=model,
                additional_authorized_imports=["inspect", "json"]
            )

            additional_instructions = """
            ADDITIONAL IMPORTANT INSTRUCTIONS:
            use the tool "final_answer" in the code block to provide the answer to the user. Prints are only for debugging purposes. So, to give your results concatenate everything you want to print in a single "final_answer" call as such : final_answer(f"your answer here").
            """

            agent.system_prompt += additional_instructions

            result = agent.run(message)
            return str(result)
            
    except Exception as e:
        return f"❌ Error: {e}\nType: {type(e).__name__}"

if __name__ == "__main__":
    demo = gr.ChatInterface(
        fn=chat_with_agent,
        type="messages",
        examples=["can you extract input/output metadata from fastqc nf-core module ?"],
        title="Agent with MCP Tools (Per-Request Connection)",
        description="This version creates a new MCP connection for each request."
    )

    demo.launch() 