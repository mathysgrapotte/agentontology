from smolagents import CodeAgent, LiteLLMModel
from smolagents.tools import ToolCollection
import gradio as gr
import modal
import sys
import subprocess
import time
# import litellm

# define modal app
app = modal.App("agent-ontology")

# define ollama image for modal
OLLAMA_IMAGE = (
    modal.Image.debian_slim()
    # pkill/pgrep come from procps
    .apt_install(
        "curl", "gnupg", "software-properties-common",
        "procps"               # ← adds pkill, pgrep, ps …
    )
    # install Ollama
    .run_commands("curl -fsSL https://ollama.com/install.sh | sh")
    # spin up daemon, pull the model, shut daemon down
    .run_commands(
        "bash -c 'ollama serve >/dev/null 2>&1 & "
        "PID=$!; "
        "sleep 10 && "
        "ollama pull devstral:latest && "
        "ollama pull qwen3:0.6b && "
        "kill $PID'"
    )
    # python deps
    .pip_install(
        "fastmcp>=2.6.1",
        "gradio[mcp]>=5.0.0",
        "huggingface_hub[mcp]>=0.32.2",
        "mcp>=1.9.2",
        "smolagents[litellm,mcp]>=1.17.0",
        "textblob>=0.19.0",
    )
)

def chat_with_agent(message, history):
    """ Function to handle chat messages and interact with the agent.
    This function creates a new MCP connection for each request, allowing the agent to use tools from the MCP server.
    """
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

def run_agent():
    """ Function to run the agent with a Gradio interface.
    This function sets up the Gradio interface and launches it.
    """
    demo = gr.ChatInterface(
        fn=chat_with_agent,
        type="messages",
        examples=["can you extract input/output metadata from fastqc nf-core module ?"],
        title="Agent with MCP Tools (Per-Request Connection)",
        description="This version creates a new MCP connection for each request."
    )
    demo.launch(share=True)

@app.function(image=OLLAMA_IMAGE, gpu="A10G", timeout=2400)
def main_remote():
    # spin up Ollama daemon in the background
    server = subprocess.Popen(["ollama", "serve"])
    time.sleep(6) # give it a moment to bind :11434
    try:
        # litellm._turn_on_debug()
        run_agent()
    finally:
        server.terminate()

def main_local():
    run_agent()

if __name__ == "__main__":
    # check if it is modal running the script or python running the script
    # if it is modal, run the remote function
    # if it is python, run the local function
    if "modal" in sys.modules:
        main_remote().remote()
    else:
        main_local()