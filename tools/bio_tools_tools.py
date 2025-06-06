import json
import requests
from smolagents import tool

@tool
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

@tool
def get_biotools_ontology(tool_name:str, entry_id:str) -> list:
    """
    Given a specific entry of the tools list associated to the module, return the biotools input ontology ID. 

    Args:
        tool_name (str): The name of the tool that gets all the associated biotools entries. 
        entry_id(str): The specific entry ID of the biotools db that best matches the nf-core module tool.
        

    Returns:
        list: The biotools ontology ID assoiated to each possible input file.
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

        found = False

        for tool in data_list:
            # Select the tool with the given entry_id
            if tool.get("name") == entry_id:
                found = True
                tool_function = tool.get("function")

                format_terms = []

                for fn in tool_function:
                    for inp in fn.get("input", []):
                        for fmt in inp.get("format", []):
                            term = fmt.get("term", "Unknown")
                            uri = fmt.get("uri", "No URI")
                            format_terms.append((term, uri))
                text_block = "List of EDAM formats used:\n"

                for i, (term, uri) in enumerate(format_terms, start=1):
                    text_block += f"{i}. {term} ({uri})\n"

                print(text_block)
                return format_terms

        if not found:
            print(f"Could not find the entry '{entry_id}' for the tool {tool_name}")
            return f"Could not find the entry '{entry_id}' for the tool {tool_name}"
    
    except requests.exceptions.RequestException as e:
        print(f"Could not find the entry '{entry_id}' for the tool {tool_name}")
        return f"Could not find bio.tools information for '{tool_name}': {e}"