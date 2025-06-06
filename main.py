import gradio as gr
from tools.meta_yml_tools import get_meta_yml_file, extract_tools_from_meta_json, extract_information_from_meta_json, extract_module_name_description
from tools.bio_tools_tools import get_biotools_response, get_biotools_ontology
from agents.query_ontology_db import agent
from agents.choose_tool_fromlist import agent as bio_tools_agent
import yaml

    
def run_multi_agent(module_name): 

    ### RETRIEVE INFORMATION FROM META.YML ###

    meta_yml = get_meta_yml_file(module_name=module_name)
    # module_info = extract_module_name_description(meta_file=meta_yml)
    # module_tools = extract_tools_from_meta_json(meta_file=meta_yml)

    # ### FIND THE MODULE TOOL ###

    # if len(module_info) == 1:
    #     module_yaml_name = module_info[0]
    #     module_description = module_info[1]
    # else:
    #     # TODO: agent to choose the right tool
    #     first_prompt = f"""
    #         The module {module_info[0]} with desciption '{module_info[1]}' contains a series of tools. 
    #         Find the tool that best describes the module. Return only one tool. Return the name. 
    #         This is the list of tools:
    #         {"\n\t".join(f"{tool[0]}: {tool[1]}" for tool in module_tools)}
    #     """
    #     module_yaml_name = "fastqc" # TODO: this would be the answer of the first agent
    #     module_description = "my description" # TODO: this would be the answer of the first agent

    # ### EXTRACT INFO FROM META.YML ###
    module_yaml_name = module_name
    meta_info = extract_information_from_meta_json(meta_file=meta_yml, tool_name=module_yaml_name)
    
    meta_info["bio_tools_id"] = ""
    ### FETCH ONOTOLOGIES FROM BIO.TOOLS ###

    if meta_info["bio_tools_id"] == "":

        second_prompt = f"""The tool {module_yaml_name} of the nf-core module {module_name} has different entries in the biotools database.
                            Find all entries associated to the tool {module_yaml_name} in the biotools database, and return a list with each entry and its description.
                            Return the list in the following format: [(entry_id, description), (entry_id, description), ...]. This can be done using the get_biotools_response tool. 
                            
                            From the list of entries in the biotools database, choose the entry that best matches the nf-core module tool {module_yaml_name}. 
                            Return the correct entry name. This you have to think. 
                            
                            Once you have the correct entry name, use it to extract the biotools input ontology ID. You can use the specific entry name and the tool name as input to the get_biotools_ontology function. 
                            Return the ontology ID in the following format: 
                            [(file_term, ontology_id), ...]. Return the answer (the list of ontologies) in a final_answer call such as final_answer([(file_term, ontology_id, ...)])."""

    result = bio_tools_agent.run(second_prompt)
    print(result)
        

        #bio_tools_list = get_biotools_response(module_yaml_name)



        # TODO: agent to select the best match from all possible bio.tools entries
        # The answer should be the entry ID
        # second_prompt = f"""The tool {module_yaml_name} has different entries in the biotools database. The list with each entry and its description
        #                     is the following: {bio_tools_list}. From this list, choose the entry that best matches the nf-core module tool""" # TODO: update
        
        # bio_tools_tool = "FastQC" # TODO: this should be the answer form the second agent

        # ontology = get_biotools_ontology(module_yaml_name, bio_tools_tool)

        ### CLASSIFY ALL INPUT AND OUTPUT ONTOLOGIES INTO THE APPROPRIATE CHANNELS ###

        # TODO !!!
        # Create an agent which classifies the ontologeis into the right i/o
        # From biotols we get a list of ontologies for inputs and a list of ontologies for outputs
        # but in most nf-core modules we will have finles separated into different channels
        # For example bam, bai, sam...
        # The agent should recieve the i/o from the module, the ontologies found in bio.tools, and assigne the correct ones to each channel.

    # ### FETCH ONTOLOGY TERMS FROM EDAM DATABASE ###

    # for input_channel in meta_info["inputs"]:
    #     for ch_element in input_channel:
    #         for key, value in ch_element.items():
    #             if key == "file":
    #                 result = agent.run(f"""
    #                     You are presentend with a file format for the type {key}, which is a {value['type']} and is described by the following description: '{value['description']}', 
    #                     search for the single best match out of possible matches in the edam ontology (formated as format_XXXX), 
    #                     and return the answer (a single ontology class) in a final_answer call such as final_answer(f'format_XXXX')
    #                 """)
    #                 print(result)
    
    ### FINAL AGENT TO BENCHMARK AND FIND THE COMMONALITIES BETWEEN BIO.TOOLS AND EDAM ###

    # TODO !!!
    # Get results from bio.tools and EDAM
    # The agent should doublecheck if results are correct (?)
    # and return the ones that make more sense
    # and remove duplicates (this can be done through a python function?)

    ### UPDATE META.YML FILE ADDING ONTOLOGIES AND RETURN THE ANSWER ###

    # # TODO: placeholder
    # # This is returning the original meta.yml, but it should return the modified one with the ontologies added
    # with open("tmp_meta.yml", "w") as fh:
    #     yaml.dump(meta_yml, fh)
    # return meta_yml, "tmp_meta.yml" # TODO: placeholder

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
    
    demo.launch()

if __name__ == "__main__":
    #run_interface()
    run_multi_agent("fastqc")  # TODO: change to final function