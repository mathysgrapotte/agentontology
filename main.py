import gradio as gr
from tools.meta_yml_tools import get_meta_yml_file, extract_tools_from_meta_json, extract_information_from_meta_json, extract_module_name_description
from tools.bio_tools_tools import get_biotools_response, get_biotools_ontology
from agents.query_ontology_db import agent
import yaml
import time
import re
import io
import logging
import threading
from contextlib import redirect_stdout, redirect_stderr
import queue
import sys
from ansi2html import Ansi2HTMLConverter as Ansi2HtmlConverter

# Global log queue for streaming logs to Gradio
log_queue = queue.Queue()

class GradioLogHandler(logging.Handler):
    """Custom logging handler that sends logs to both terminal and Gradio queue"""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        self.terminal_handler = logging.StreamHandler(sys.__stdout__)
        self.terminal_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
    
    def emit(self, record):
        # Send to terminal
        self.terminal_handler.emit(record)
        
        # Send to Gradio queue
        try:
            log_msg = self.format(record)
            self.log_queue.put(log_msg)
        except Exception:
            pass

class QueueWriter:
    """A stream-like object that writes to a queue, to capture stdout."""
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        # Print raw output to terminal to preserve colors
        sys.__stdout__.write(text)
        sys.__stdout__.flush()

        # Put the raw text with ANSI codes into the queue for HTML conversion
        self.queue.put(text)

    def flush(self):
        # Also flush stdout
        sys.__stdout__.flush()

def setup_logging():
    """Setup logging to capture smolagents logs"""
    # Create custom handler
    gradio_handler = GradioLogHandler(log_queue)
    gradio_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Configure smolagents logger
    smolagents_logger = logging.getLogger("smolagents")
    smolagents_logger.setLevel(logging.INFO)
    smolagents_logger.addHandler(gradio_handler)
    
    # Also capture other relevant loggers that might be used
    for logger_name in ["transformers", "huggingface_hub", "agents"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.addHandler(gradio_handler)
    
    return gradio_handler

# Initialize logging setup
log_handler = setup_logging()

def extract_format_terms_from_result(result):
    """Extract EDAM format terms from agent result string"""
    if isinstance(result, str):
        # Look for format_XXXX patterns in the result using regex
        format_matches = re.findall(r'format_\d+', result)
        return format_matches
    elif isinstance(result, list):
        # If it's already a list, filter for format terms
        return [item for item in result if isinstance(item, str) and item.startswith('format_')]
    return []

def format_ontology_results_html(results, meta_yml):
    """Format the ontology results into a nice HTML display with clickable links"""
    
    if not results.get("input"):
        return "<div class='no-results'>No ontology results found.</div>"
    
    html_content = """
    <div class='ontology-results'>
        <div class='results-header'>
            <h2> Discovered EDAM Ontologies</h2>
            <p>Click on any ontology term to view detailed information in the EDAM database</p>
        </div>
    """
    
    # Group inputs by their descriptions from meta_yml
    input_info = {}
    for input_channel in meta_yml.get("input", []):
        for ch_element in input_channel:
            for key, value in ch_element.items():
                if value.get("type") == "file":
                    input_info[key] = value.get("description", "No description available")
    
    for input_name, result in results["input"].items():
        format_terms = extract_format_terms_from_result(result)
        description = input_info.get(input_name, "No description available")
        
        html_content += f"""
        <div class='input-section'>
            <div class='input-header'>
                <h3>{input_name}</h3>
                <p class='input-description'>{description}</p>
            </div>
            <div class='ontologies-container'>
        """
        
        if format_terms:
            for term in format_terms:
                term_id = term.replace("format_", "")
                link_url = f"http://edamontology.org/{term}"
                html_content += f"""
                <div class='ontology-card'>
                    <a href='{link_url}' target='_blank' class='ontology-link'>
                        <div class='ontology-icon'>🔗</div>
                        <div class='ontology-details'>
                            <span class='ontology-id'>{term}</span>
                            <span class='ontology-label'>Click to view in EDAM database</span>
                        </div>
                    </a>
                </div>
                """
        else:
            html_content += """
            <div class='no-ontologies'>
                <span>⚠️ No EDAM format ontologies found for this input</span>
            </div>
            """
        
        html_content += """
            </div>
        </div>
        """
    
    html_content += "</div>"
    
    return html_content

def run_multi_agent_with_logs(module_name):
    """Enhanced function with progress tracking and live log streaming"""
    
    # Clear the log queue before starting
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break
    
    results = {"input": {}, "output": {}}
    meta_yml = None
    
    try:
        ### RETRIEVE INFORMATION FROM META.YML ###
        meta_yml = get_meta_yml_file(module_name=module_name)
        time.sleep(0.5)

        ### FETCH ONTOLOGY TERMS FROM EDAM DATABASE ###
        total_inputs = len(meta_yml.get("input", []))
        current_input = 0
        
        for input_channel in meta_yml["input"]:
            current_input += 1
            
            for ch_element in input_channel:
                for key, value in ch_element.items():
                    if value["type"] == "file":
                        # This is where the agent runs - logs should be captured automatically
                        result = agent.run(f"You are presentend with a file format for the input {key}, which is a file and is described by the following description: '{value['description']}', search for the best matches out of possible matches in the edam ontology (formated as format_XXXX), and return the answer (a list of ontology classes) in a final_answer call such as final_answer([format_XXXX, format_XXXX, ...])")
                        results["input"][key] = result
                        
                        format_terms = extract_format_terms_from_result(result)

        ### UPDATE META.YML FILE ADDING ONTOLOGIES AND RETURN THE ANSWER ###
        with open("tmp_meta.yml", "w") as fh:
            yaml.dump(meta_yml, fh)
        
    except Exception as e:
        raise e
    
    # Format the results into a nice HTML display
    formatted_results = format_ontology_results_html(results, meta_yml)
    
    return formatted_results, "tmp_meta.yml"

def stream_logs_and_run_agent(module_name):
    """Generator function that streams logs while running the agent"""
    
    # Start the agent in a separate thread
    result_container = {"ontology_output": None, "file_output": None, "error": None}
    
    def run_agent_thread():
        try:
            queue_writer = QueueWriter(log_queue)
            with redirect_stdout(queue_writer), redirect_stderr(queue_writer):
                ontology_output, file_output = run_multi_agent_with_logs(module_name)
                result_container["ontology_output"] = ontology_output
                result_container["file_output"] = file_output
        except Exception as e:
            # The error will be redirected to the queue via stderr
            result_container["error"] = str(e)
    
    # Start the thread
    agent_thread = threading.Thread(target=run_agent_thread)
    agent_thread.start()
    
    # Stream logs while the agent is running
    accumulated_logs = ""
    converter = Ansi2HtmlConverter(dark_bg=True, line_wrap=False)

    while agent_thread.is_alive() or not log_queue.empty():
        try:
            # Get log message with a short timeout
            log_msg = log_queue.get(timeout=0.1)
            accumulated_logs += log_msg
            
            # Yield the updated logs
            html_logs = converter.convert(accumulated_logs, full=False)
            yield f"<div class='live-logs-container'><pre class='live-logs'>{html_logs}</pre></div>", None, None
            
        except queue.Empty:
            # If no new logs and thread is still alive, yield current state
            if agent_thread.is_alive():
                html_logs = converter.convert(accumulated_logs, full=False)
                yield f"<div class='live-logs-container'><pre class='live-logs'>{html_logs}</pre></div>", None, None
            continue
    
    # Wait for the thread to complete
    agent_thread.join()
    
    # Check for any remaining logs
    while not log_queue.empty():
        try:
            log_msg = log_queue.get_nowait()
            accumulated_logs += log_msg + "\n"
        except queue.Empty:
            break
    
    # Return final results
    html_logs = converter.convert(accumulated_logs, full=False)
    if result_container["error"]:
        yield f"<div class='live-logs-container'><pre class='live-logs'>{html_logs}</pre></div>", None, None
    else:
        yield f"<div class='live-logs-container'><pre class='live-logs'>{html_logs}</pre></div>", result_container["ontology_output"], result_container["file_output"]

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
    
    /* Live logs styling */
    .live-logs-container {
        background: #212529 !important;
        border: 2px solid rgba(36, 176, 100, 0.4) !important;
        border-radius: 15px !important;
        color: #e9ecef !important;
        font-family: 'Fira Code', 'Monaco', 'Consolas', monospace !important;
        font-size: 0.9rem !important;
        line-height: 1.4 !important;
        max-height: 400px !important;
        overflow-y: auto !important;
        padding: 1rem !important;
        margin: 0 auto !important;
        width: 95% !important;
        text-align: center !important;
    }

    .live-logs {
        white-space: pre-wrap !important;
        word-wrap: break-word;
        display: inline-block !important;
        text-align: left !important;
    }
    
    .live-logs-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .live-logs-container::-webkit-scrollbar-track {
        background: rgba(52, 58, 64, 0.5);
        border-radius: 4px;
    }
    
    .live-logs-container::-webkit-scrollbar-thumb {
        background: rgba(36, 176, 100, 0.6);
        border-radius: 4px;
    }
    
    .live-logs-container::-webkit-scrollbar-thumb:hover {
        background: rgba(36, 176, 100, 0.8);
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
    
    /* Ontology Results Styling */
    .ontology-results {
        background: rgba(33, 37, 41, 0.95) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        border: 2px solid rgba(36, 176, 100, 0.4) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .results-header {
        text-align: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(36, 176, 100, 0.3);
    }
    
    .results-header h2 {
        color: #24B064 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin: 0 0 0.5rem 0 !important;
    }
    
    .results-header p {
        color: #adb5bd !important;
        font-size: 1rem !important;
        margin: 0 !important;
    }
    
    .input-section {
        background: rgba(52, 58, 64, 0.8) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        border: 1px solid rgba(36, 176, 100, 0.3) !important;
    }
    
    .input-header h3 {
        color: #24B064 !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        margin: 0 0 0.5rem 0 !important;
    }
    
    .input-description {
        color: #e9ecef !important;
        font-size: 0.95rem !important;
        margin: 0 0 1rem 0 !important;
        font-style: italic;
        line-height: 1.4;
    }
    
    .ontologies-container {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .ontology-card {
        background: rgba(33, 37, 41, 0.9) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(36, 176, 100, 0.4) !important;
        overflow: hidden;
        transition: all 0.3s ease !important;
    }
    
    .ontology-card:hover {
        border-color: #24B064 !important;
        box-shadow: 0 4px 15px rgba(36, 176, 100, 0.3) !important;
        transform: translateY(-2px);
    }
    
    .ontology-link {
        display: flex !important;
        align-items: center !important;
        padding: 1rem !important;
        text-decoration: none !important;
        color: inherit !important;
    }
    
    .ontology-link:hover {
        background: rgba(36, 176, 100, 0.1) !important;
    }
    
    .ontology-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
        color: #24B064;
    }
    
    .ontology-details {
        display: flex;
        flex-direction: column;
        flex: 1;
    }
    
    .ontology-id {
        color: #24B064 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin-bottom: 0.25rem;
    }
    
    .ontology-label {
        color: #adb5bd !important;
        font-size: 0.9rem !important;
    }
    
    .no-ontologies {
        background: rgba(255, 193, 7, 0.1) !important;
        border: 1px solid rgba(255, 193, 7, 0.3) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        text-align: center;
    }
    
    .no-ontologies span {
        color: #ffc107 !important;
        font-weight: 500;
    }
    
    .no-results {
        background: rgba(220, 53, 69, 0.1) !important;
        border: 1px solid rgba(220, 53, 69, 0.3) !important;
        border-radius: 8px !important;
        padding: 2rem !important;
        text-align: center;
        color: #dc3545 !important;
        font-size: 1.1rem;
        font-weight: 500;
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
                    nf-core module
                </div>
                """)
                
                # create the input textbox for the nf-core module name
                module_input = gr.Textbox(
                    label="nf-core module name", 
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

            with gr.Column(scale=1, elem_classes="output-container"):
                gr.HTML("""
                <div class="section-header">
                    discovered ontologies
                </div>
                """)
                
                # create the output HTML component for the ontology results
                ontology_output = gr.HTML(
                    label="discovered EDAM ontologies",
                    elem_classes="result-container"
                )
                
                download_button = gr.File(
                    label="download original meta.yml with ontologies",
                    elem_classes="result-container"
                )
        
        # Live logs section
        with gr.Row():
            with gr.Column(elem_classes="input-container"):
                gr.HTML("""
                <div class="section-header">
                    🦙 live agent logs
                </div>
                """)
                
                # Live log display
                live_logs = gr.HTML(
                    "<div class='live-logs-container'><pre class='live-logs'>Logs will appear here...</pre></div>",
                    label="smolagents live logs"
                )

        # Event handling for the streaming logs
        def clear_outputs():
            """Clear all outputs when starting a new analysis"""
            return "", "", None
        
        # Set the function to run when the button is clicked
        fetch_btn.click(
            fn=clear_outputs,
            outputs=[live_logs, ontology_output, download_button]
        ).then(
            fn=stream_logs_and_run_agent,
            inputs=module_input,
            outputs=[live_logs, ontology_output, download_button]
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
    
    demo.launch(debug=True)

if __name__ == "__main__":
    run_interface()