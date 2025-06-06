from smolagents import CodeAgent, LiteLLMModel
from tools.bio_tools_tools import get_biotools_response, get_biotools_ontology_input, get_biotools_ontology_output

model = LiteLLMModel(
    # model_id="ollama/devstral:latest",
    model_id="ollama/devstral:latest",
    api_base="http://localhost:11434",
    temperature=0.0,
    max_tokens=5000,
)

tool_list = [get_biotools_response, get_biotools_ontology_input, get_biotools_ontology_output]

agent = CodeAgent(
    tools=tool_list,
    model=model,
    additional_authorized_imports=["inspect", "json"]
)