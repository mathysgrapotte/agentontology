from smolagents import CodeAgent, LiteLLMModel
from smolagents.tools import ToolCollection
import gradio as gr
import requests
from tools.meta_yml_tools import get_meta_yml_file, extract_tools_from_meta_json, extract_information_from_meta_json, extract_module_name_description

def main(module_name): 
    meta_yml = get_meta_yml_file(module_name=module_name)
    module_info = extract_module_name_description(meta_file=meta_yml)
    module_tools = extract_tools_from_meta_json(meta_file=meta_yml)
    # TODO: agent to choose the right tool
    # Only call the agent if there is more than one tool, otherwise get the first name
    first_prompt = f"""
        The module {module_info[0]} with desciption '{module_info[1]}' contains a series of tools. 
        Find the tool that best describes the module. Return only one tool. Return the name. 
        This is the list of tools:
        {"\n\t".join(f"{tool[0]}: {tool[1]}" for tool in module_tools)}
    """
    tool_name = "fastqc" # this would be the answer of the first agent
    meta_info = extract_information_from_meta_json(meta_file=meta_yml, tool_name=tool_name)

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

# TODO: placeholder function
def fetch_meta_yml(module_name):
    # Adjust the URL or path to your actual source of nf-core modules
    base_url = f"https://raw.githubusercontent.com/nf-core/modules/refs/heads/master/modules/nf-core/{module_name}/meta.yml"
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        content = response.text

        # Save for download
        with open("meta.yml", "w") as f:
            f.write(content)

        return content, "meta.yml"
    except Exception as e:
        return f"Error: Could not retrieve meta.yml for module '{module_name}'\n{e}", None

if __name__ == "__main__":
    with gr.Blocks() as demo:
        gr.Markdown("### 🔍 Update an nf-core module `meta.yml` file by adding EDAM ontology terms.")

        with gr.Row():
            module_input = gr.Textbox(label="nf-core Module Name", placeholder="e.g. fastqc")

        fetch_btn = gr.Button("Update meta.yml")

        with gr.Row():
            meta_output = gr.Textbox(label="meta.yml content", lines=20)
            download_button = gr.File(label="Download meta.yml")

        fetch_btn.click(
            fn=fetch_meta_yml, # TODO: change to final function
            inputs=module_input,
            outputs=[meta_output, download_button]
        )

    demo.launch()