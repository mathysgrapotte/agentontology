import requests
import yaml


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

    if subtool != "":
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

def update_meta_yml(input_ontologies: dict, output_ontologies: dict, meta_yml:dict) -> dict:
    """
    Update the meta.yml file with the final obtained ontologies

    Args:
        input_ontologies (dict): The final ontologies for inputs. 
                            The dictionary contains the name of the file as key and a list of ontologies as value.
        output_ontologies (dict): The final ontologies for outputs. 
                            The dictionary contains the name of the file as key and a list of ontologies as value.
        meta_yml (dict): The original meta.yml file content to be modified

    Returns:
        (dict): The updated meta.yml file
    """
    # Format ontology links
    for key in input_ontologies.keys():
        updated_list = []
        for format in input_ontologies[key]:
            updated_list.append({"edam": f"http://edamontology.org/{format}"})
        input_ontologies[key] = updated_list


    # inputs
    for i, input_ch in enumerate(meta_yml["input"]):
        for j, ch_element in enumerate(input_ch):
            for key, value in ch_element.items():
                if key in input_ontologies:
                    try:
                        meta_yml["input"][i][j][key]["ontologies"].append(input_ontologies[key])
                    except KeyError:
                        meta_yml["input"][i][j][key]["ontologies"] = input_ontologies[key]
    # outputs
    # for key,
    
    return meta_yml