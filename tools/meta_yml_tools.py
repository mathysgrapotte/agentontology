import requests
import json
import yaml

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

def get_meta_yml_file(module_name: str) -> dict:
    """
    Access the nf-core/modules repository and return the meta.yml file of the given module.
    
    Args:
        module_name (str): The name of the module to get the meta.yml file for. 
                            The module_name must be provided in the format <tool>_<subtool> or <tool>/<subtool> or <tool> <subtool>.
                            The subtool is optional.
                            For example, "bwa_align" or "fastqc" or "bwa align" or "bwa/align".
    Returns:
        dict: The meta.yml file of the given module in json/yaml format as a dictionary.
    """
    if "_" in module_name:
        tool, subtool = module_name.split("_")
    elif "/" in module_name:
        tool, subtool = module_name.split("/")
    elif " " in module_name:
        tool, subtool = module_name.split(" ")
    else:
        tool, subtool = module_name, ""

    if subtool:
        url = f"https://raw.githubusercontent.com/nf-core/modules/refs/heads/master/modules/nf-core/{tool}/{subtool}/meta.yml"
    else:
        url = f"https://raw.githubusercontent.com/nf-core/modules/refs/heads/master/modules/nf-core/{tool}/meta.yml"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        return yaml.safe_load(response.text)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"An error occurred while connecting to the URL: {url}. Error message: {e}")

def extract_module_name_description(meta_file: dict) -> list:
    """
    Extract the name and description of the module from the meta.yml file.

    Args:
        meta_file (str): The content of the module meta.yml file in json format.

    Returns:
        list: A list containing two elements, the module name and the module description.
    """
    name = meta_file.get("name", "")
    description = meta_file.get("description", "")
    return [name, description]

def extract_tools_from_meta_json(meta_file: dict) -> list[list]:
    """
    Extract the tools and description from the meta.yml file.

    Args:
        meta_file (str): The content of the module meta.yml file in json format.

    Returns:
        list: A list of lists. Each element of the list is one tool, the sub-list contains two elements, the name and description of the tool.
    """
    module_tools = []
    tools_list = meta_file.get("tools", [])
    for tool in tools_list:
        name = list(tool.keys())[0]
        description = tool[name].get("description", "")
        module_tools.append([name, description])
    return module_tools

def extract_information_from_meta_json(meta_file: dict, tool_name: str) -> dict:
    """
    Extract information metadata from an nf-core module meta.yml file.
    Information extracted:
        - inputs
        - outputs
        - homepage URL
        - documentation URL
        - bio.tools ID
        

    Args:
        meta_file (str): The content of the module meta.yml file in json format.
        tool_name (str): The name of the tool to extract information for.

    Returns:
        dict: A dictionary with the extracted metadata.
            Each file or term can also contain additional metadata like 'description' or 'type'.

    Example output:
        {
            "inputs": [...],
            "outputs": [...],
            "homepage": "https://www.bioinformatics.babraham.ac.uk/projects/fastqc/",
            "documentation": "https://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/",
            "bio_tools_id": "biotools:fastqc"
        }
    """
    inputs = meta_file.get("input", [])
    outputs = meta_file.get("output", [])
    for tool in meta_file.get("tools", []):
        if list(tool.keys())[0] == tool_name:
            homepage_url = tool.get("homepage", "")
            documentation_rul = tool.get("documentation", "")
            bio_tools_id = tool.get("identifier", "")
        print("Extracted metadata information from nf-core module meta.yml")
    return {"inputs": inputs, "outputs": outputs, "homepage": homepage_url, "documentation": documentation_rul, "bio_tools_id": bio_tools_id}


def get_biotools_response(tool_name: str) -> list:
    """
    Try to get bio.tools information for a tool.

    Args:
        tool_name (str): The name of the tool to get the bio.tools information for.

    Returns:
        list: A list with all the entries in biotools associated to the name of the tool and its description.
    """
    url = f"https://bio.tools/api/t/?q={tool_name}&format=json"
    try:
        # Send a GET request to the API
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        # Parse the JSON response
        data = response.text
        data = json.loads(data)
        data_list = data.get("list", [])
        tool_info = [(tool.get("name"), tool.get("description", "")) for tool in data_list]

        for name, desc in tool_info:
            print(f"Tool: {name}\nDescription: {desc}\n")

        print(f"Found bio.tools information for '{tool_name}'")
        return tool_info

    except requests.exceptions.RequestException as e:
        print(f"Could not find bio.tools information for '{tool_name}': {e}")
        return f"Could not find bio.tools information for '{tool_name}': {e}"