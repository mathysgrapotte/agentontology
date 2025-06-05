import gradio as gr
from tools.meta_yml_tools import get_meta_yml_file, extract_tools_from_meta_json, extract_information_from_meta_json, extract_module_name_description, get_biotools_response
from agents.query_ontology_db import agent

    
def run_multi_agent(module_name): 
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
    for input_tool in module_info["inputs"]:
        for key, value in input_tool.items():
            if key == "file":
                result = agent.run(f"you are presentend with a file format for the type {key}, which is a {value['type']} and is described by the following description: '{value['description']}', search for the single best match out of possible matches in the edam ontology (formated as format_XXXX), and return the answer (a single ontology class) in a final_answer call such as final_answer(f'format_XXXX')")
                print(result)
    
    # TODO: placeholder
    # This is returning the original meta.yml, but it should return the modified one with the ontologies added
    with open("tmp_meta.yml", "w") as fh:
        fh.write(meta_info)
    return meta_info, "tmp_meta.yml" # TODO: placeholder

def run_interface():
    """ Function to run the agent with a Gradio interface.
    This function sets up the Gradio interface and launches it.
    """
    # create the Gradio interface
    with gr.Blocks() as demo:
        gr.Markdown("### 🔍 Update an nf-core module `meta.yml` file by adding EDAM ontology terms.")

        # create the input textbox for the nf-core module name
        module_input = gr.Textbox(label="nf-core Module Name", placeholder="e.g. fastqc")

        # create the button to fetch the meta.yml file
        fetch_btn = gr.Button("Update meta.yml")

        # create the output textbox for the meta.yml content and a download button
        meta_output = gr.Textbox(label="meta.yml content", lines=20)
        download_button = gr.File(label="Download meta.yml")

        # set the function to run when the button is clicked
        fetch_btn.click(
            fn=run_multi_agent,  # TODO: change to final function
            inputs=module_input,
            outputs=[meta_output, download_button]
        )
    
    demo.launch(share=True)

if __name__ == "__main__":
    run_interface()