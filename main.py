import gradio as gr
from tools.meta_yml_tools import get_meta_yml_file, extract_tools_from_meta_json, extract_information_from_meta_json, extract_module_name_description
from tools.bio_tools_tools import get_biotools_response, get_biotools_ontology
from agents.query_ontology_db import agent
import yaml
import time

    
def run_multi_agent(module_name, progress=gr.Progress()): 
    """Enhanced function with progress tracking"""
    
    progress(0, desc="🦙 Llama is waking up...")
    time.sleep(0.5)
    
    ### RETRIEVE INFORMATION FROM META.YML ###
    progress(0.1, desc="🔍 Fetching meta.yml file...")
    meta_yml = get_meta_yml_file(module_name=module_name)
    time.sleep(0.5)
    
    progress(0.2, desc="🦙 Llama is analyzing the module structure...")
    # module_info = extract_module_name_description(meta_file=meta_yml)
    # module_tools = extract_tools_from_meta_json(meta_file=meta_yml)
    time.sleep(0.5)

    # ### FIND THE MODULE TOOL ###
    progress(0.3, desc="🧠 Llama is thinking about the best tool...")
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
    progress(0.4, desc="📊 Extracting metadata information...")
    # meta_info = extract_information_from_meta_json(meta_file=meta_yml, tool_name=module_yaml_name)
    time.sleep(0.5)

    # ### FETCH ONOTOLOGIES FROM BIO.TOOLS ###
    progress(0.5, desc="🔬 Searching bio.tools database...")
    # if meta_info["bio_tools_id"] == "":
    #     bio_tools_list = get_biotools_response(module_yaml_name)

    #     # TODO: agent to select the best match from all possible bio.tools entries
    #     # The answer should be the entry ID
    #     second_prompt = "" # TODO: update
    #     bio_tools_tool = "FastQC" # TODO: this should be the answer form the second agent

    #     ontology = get_biotools_ontology(module_yaml_name, bio_tools_tool)

    #     ### CLASSIFY ALL INPUT AND OUTPUT ONTOLOGIES INTO THE APPROPRIATE CHANNELS ###

    #     # TODO !!!
    #     # Create an agent which classifies the ontologeis into the right i/o
    #     # From biotols we get a list of ontologies for inputs and a list of ontologies for outputs
    #     # but in most nf-core modules we will have finles separated into different channels
    #     # For example bam, bai, sam...
    #     # The agent should recieve the i/o from the module, the ontologies found in bio.tools, and assigne the correct ones to each channel.

    # ### FETCH ONTOLOGY TERMS FROM EDAM DATABASE ###
    progress(0.6, desc="🦙 Llama is consulting the EDAM database...")
    results = {"input": {}, "output": {}}

    total_inputs = len(meta_yml.get("input", []))
    current_input = 0
    
    for input_channel in meta_yml["input"]:
        current_input += 1
        progress(0.6 + (current_input / total_inputs) * 0.3, 
                desc=f"🔍 Processing input channel {current_input}/{total_inputs}...")
        
        for ch_element in input_channel:
            for key, value in ch_element.items():
                if value["type"] == "file":
                    progress(0.6 + (current_input / total_inputs) * 0.3, 
                            desc=f"🦙 Llama is analyzing {key}...")
                    result = agent.run(f"You are presentend with a file format for the input {key}, which is a file and is described by the following description: '{value['description']}', search for the best matches out of possible matches in the edam ontology (formated as format_XXXX), and return the answer (a list of ontology classes) in a final_answer call such as final_answer([format_XXXX, format_XXXX, ...])")
                    results["input"][key] = result

    # for output_channel in meta_info["outputs"]:
    #     for ch_element in output_channel:
    #         for key, value in ch_element.items():
    #             if value["type"] == "file":
    #                 result = agent.run(f"You are presentend with a file format for the output {key}, which is a file and is described by the following description: '{value['description']}', search for the best matches out of possible matches in the edam ontology (formated as format_XXXX), and return the answer (a list of ontology classes) in a final_answer call such as final_answer([format_XXXX, format_XXXX, ...])")
    #                 results["outputs"][key] = result
    
    ### FINAL AGENT TO BENCHMARK AND FIND THE COMMONALITIES BETWEEN BIO.TOOLS AND EDAM ###
    progress(0.9, desc="🔄 Finalizing ontology mappings...")
    # TODO !!!
    # Get results from bio.tools and EDAM
    # The agent should doublecheck if results are correct (?)
    # and return the ones that make more sense
    # and remove duplicates (this can be done through a python function?)

    ### UPDATE META.YML FILE ADDING ONTOLOGIES AND RETURN THE ANSWER ###
    progress(0.95, desc="💾 Generating updated meta.yml...")
    # TODO: placeholder
    # This is returning the original meta.yml, but it should return the modified one with the ontologies added
    with open("tmp_meta.yml", "w") as fh:
        yaml.dump(meta_yml, fh)
    
    progress(1.0, desc="✅ Llama has finished! Meta.yml updated successfully!")
    time.sleep(0.5)
    
    return meta_yml, "tmp_meta.yml" # TODO: placeholder

def run_interface():
    """ Function to run the agent with a Gradio interface.
    This function sets up the Gradio interface and launches it.
    """
    
    # Custom theme with nf-core colors
    custom_theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.Color(
            c50="#f0fdf4",   # Very light green
            c100="#dcfce7",  # Light green
            c200="#bbf7d0",  # Lighter green
            c300="#86efac",  # Light nf-core green
            c400="#4ade80",  # Medium green
            c500="#24B064",  # Official nf-core green
            c600="#16a34a",  # Darker green
            c700="#396E35",  # nf-core dark green
            c800="#166534",  # Very dark green
            c900="#14532d",  # Darkest green
            c950="#0f2419",  # Ultra dark green
        ),
        secondary_hue=gr.themes.colors.Color(
            c50="#fefce8",   # Very light yellow
            c100="#fef3c7",  # Light yellow
            c200="#fde68a",  # Lighter yellow
            c300="#fcd34d",  # Light yellow
            c400="#f59e0b",  # Medium yellow
            c500="#ECDC86",  # nf-core yellow
            c600="#d97706",  # Darker yellow
            c700="#b45309",  # Dark yellow
            c800="#92400e",  # Very dark yellow
            c900="#78350f",  # Darkest yellow
            c950="#451a03",  # Ultra dark yellow
        ),
        neutral_hue=gr.themes.colors.Color(
            c50="#f8f9fa",   # Bootstrap gray-100
            c100="#e9ecef",  # Bootstrap gray-200
            c200="#dee2e6",  # Bootstrap gray-300
            c300="#ced4da",  # Bootstrap gray-400
            c400="#adb5bd",  # Bootstrap gray-500
            c500="#6c757d",  # Bootstrap gray-600
            c600="#495057",  # Bootstrap gray-700
            c700="#343a40",  # Bootstrap gray-800
            c800="#212529",  # Bootstrap gray-900 (main nf-core background)
            c900="#3F2B29",  # nf-core brown
            c950="#1a1411",  # Ultra dark brown
        ),
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        radius_size="lg",
        spacing_size="md"
    )
    
    # Custom CSS with nf-core branding
    custom_css = """
    /* Main container styling with nf-core colors */
    .gradio-container {
        background: linear-gradient(135deg, #24B064 0%, #396E35 50%, #3F2B29 100%) !important;
        min-height: 100vh;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: rgba(33, 37, 41, 0.95);
        border-radius: 20px;
        margin: 1rem 0 2rem 0;
        backdrop-filter: blur(10px);
        border: 2px solid rgba(36, 176, 100, 0.5);
        box-shadow: 0 8px 32px rgba(36, 176, 100, 0.3);
    }
    
    .main-header h1 {
        color: #24B064 !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        text-shadow: 0 2px 4px rgba(36, 176, 100, 0.3);
    }
    
    .main-header p {
        color: #e9ecef !important;
        font-size: 1.1rem !important;
        margin: 0.5rem 0 0 0 !important;
    }
    
    .nf-core-logo {
        width: 60px;
        height: 60px;
        margin: 0 auto 1rem auto;
        display: block;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
    }
    
    /* Custom Llama Spinner with nf-core styling */
    @keyframes llamaRun {
        0% { transform: translateX(-20px) rotate(-5deg); }
        50% { transform: translateX(20px) rotate(5deg); }
        100% { transform: translateX(-20px) rotate(-5deg); }
    }
    
    @keyframes llamaBounce {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes nfCoreGlow {
        0%, 100% { box-shadow: 0 8px 32px rgba(36, 176, 100, 0.3); }
        50% { box-shadow: 0 8px 32px rgba(36, 176, 100, 0.6); }
    }
    
    .llama-loader {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: rgba(52, 58, 64, 0.95);
        border-radius: 20px;
        margin: 1rem;
        border: 2px solid #24B064;
        animation: nfCoreGlow 2s ease-in-out infinite;
        backdrop-filter: blur(10px);
    }
    
    .llama-emoji {
        font-size: 4rem;
        animation: llamaRun 2s ease-in-out infinite, llamaBounce 1s ease-in-out infinite;
        margin-bottom: 1rem;
        filter: drop-shadow(0 4px 8px rgba(36, 176, 100, 0.3));
    }
    
    .llama-text {
        font-size: 1.2rem;
        color: #24B064;
        font-weight: 600;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .llama-subtext {
        font-size: 0.9rem;
        color: #ECDC86;
        text-align: center;
        font-style: italic;
    }
    
    /* Input/Output styling with dark nf-core theme */
    .input-container, .output-container {
        background: rgba(52, 58, 64, 0.95) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        border: 2px solid rgba(36, 176, 100, 0.4) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .input-container:hover, .output-container:hover {
        border-color: #24B064 !important;
        box-shadow: 0 6px 25px rgba(36, 176, 100, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Button styling with nf-core green */
    .btn-primary {
        background: linear-gradient(45deg, #24B064, #396E35) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(36, 176, 100, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: none !important;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(36, 176, 100, 0.6) !important;
        background: linear-gradient(45deg, #396E35, #24B064) !important;
    }
    
    /* Progress bar with nf-core colors */
    .progress-bar {
        background: linear-gradient(90deg, #24B064, #ECDC86) !important;
    }
    
    /* Textbox styling with dark theme */
    .gr-textbox {
        border-radius: 10px !important;
        border: 2px solid rgba(36, 176, 100, 0.3) !important;
        transition: all 0.3s ease !important;
        background: rgba(33, 37, 41, 0.9) !important;
        color: #e9ecef !important;
    }
    
    .gr-textbox:focus {
        border-color: #24B064 !important;
        box-shadow: 0 0 0 3px rgba(36, 176, 100, 0.2) !important;
    }
    
    /* Section headers with dark theme */
    .section-header {
        color: #24B064 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #24B064 !important;
        padding-bottom: 0.5rem !important;
        margin-bottom: 1rem !important;
        font-size: 1.1rem !important;
    }
    
    /* Labels and text in dark theme */
    .gr-box label {
        color: #e9ecef !important;
    }
    
    .gr-box .gr-text-sm {
        color: #adb5bd !important;
    }
    
    /* Animation for results */
    @keyframes slideInUp {
        from {
            transform: translateY(30px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    .result-container {
        animation: slideInUp 0.5s ease-out;
        border: 1px solid #24B064 !important;
        background: rgba(33, 37, 41, 0.9) !important;
    }
    
    .result-container textarea {
        background: rgba(33, 37, 41, 0.9) !important;
        color: #e9ecef !important;
        border: 1px solid rgba(36, 176, 100, 0.3) !important;
    }
    
    /* Footer with nf-core styling */
    .nf-core-footer {
        background: rgba(63, 43, 41, 0.95) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        margin: 2rem 0 1rem 0 !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(36, 176, 100, 0.4) !important;
    }
    
    .nf-core-footer p {
        color: rgba(255, 255, 255, 0.9) !important;
        margin: 0 !important;
    }
    
    .nf-core-footer strong {
        color: #ECDC86 !important;
    }
    
    /* File component dark theme */
    .gr-file {
        background: rgba(33, 37, 41, 0.9) !important;
        border: 1px solid rgba(36, 176, 100, 0.3) !important;
        color: #e9ecef !important;
    }
    """
    
    # create the Gradio interface
    with gr.Blocks(theme=custom_theme, css=custom_css, title="🦙 nf-core Ontology Assistant") as demo:
        
        # Header with nf-core logo
        gr.HTML("""
        <div class="main-header">
            <img src="https://raw.githubusercontent.com/nf-core/logos/master/nf-core-logos/nf-core-logo-square.png" class="nf-core-logo" alt="nf-core logo">
            <h1>🦙 nf-core Ontology Assistant</h1>
            <p>Intelligent nf-core meta.yml enhancement with EDAM ontology terms</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1, elem_classes="input-container"):
                gr.HTML("""
                <div class="section-header">
                    📝 Module Configuration
                </div>
                """)
                
                # create the input textbox for the nf-core module name
                module_input = gr.Textbox(
                    label="🔧 nf-core Module Name", 
                    placeholder="e.g. fastqc, samtools, bwa...",
                    info="Enter the name of the nf-core module you want to enhance",
                    elem_classes="gr-textbox"
                )

                # create the button to fetch the meta.yml file
                fetch_btn = gr.Button(
                    "🚀 Start nf-core Analysis", 
                    variant="primary",
                    elem_classes="btn-primary",
                    size="lg"
                )
                
                # Llama status indicator
                status_display = gr.HTML(visible=False)

            with gr.Column(scale=1, elem_classes="output-container"):
                gr.HTML("""
                <div class="section-header">
                    📊 Enhanced Results
                </div>
                """)
                
                # create the output textbox for the meta.yml content and a download button
                meta_output = gr.Textbox(
                    label="📄 Updated meta.yml content", 
                    lines=15,
                    interactive=False,
                    elem_classes="result-container"
                )
                
                download_button = gr.File(
                    label="💾 Download Enhanced meta.yml",
                    elem_classes="result-container"
                )

        # Progress indicator function
        def show_llama_status():
            return gr.HTML("""
            <div class="llama-loader">
                <div class="llama-emoji">🦙</div>
                <div class="llama-text">nf-core Llama is working hard!</div>
                <div class="llama-subtext">Analyzing ontologies and enhancing your meta.yml...</div>
            </div>
            """, visible=True)
        
        def hide_llama_status():
            return gr.HTML("", visible=False)

        # set the function to run when the button is clicked
        fetch_btn.click(
            fn=show_llama_status,
            outputs=status_display
        ).then(
            fn=run_multi_agent,
            inputs=module_input,
            outputs=[meta_output, download_button],
            show_progress="full"
        ).then(
            fn=hide_llama_status,
            outputs=status_display
        )
        
        # Footer with nf-core branding
        gr.HTML("""
        <div class="nf-core-footer">
            <p style="text-align: center;">
                🔬 <strong>Powered by nf-core, EDAM Ontology & bio.tools</strong>
                <br>
                Built with ❤️ and 🦙 for the nf-core community
            </p>
        </div>
        """)
    
    demo.launch()

if __name__ == "__main__":
    run_interface()