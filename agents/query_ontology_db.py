from smolagents import CodeAgent, LiteLLMModel
from tools.fetch_ontology_tools import search_edam_ontology_by_search_term, get_edam_description_from_ontology_format_class

model = LiteLLMModel(
    model_id="ollama/devstral:latest",
    #model_id="ollama/qwen3:0.6b",
    api_base="http://localhost:11434",
    temperature=0.0,
    max_tokens=8000,
    num_ctx=9000,
)

tool_list = [search_edam_ontology_by_search_term, get_edam_description_from_ontology_format_class]

agent = CodeAgent(
    tools=tool_list,
    model=model,
    additional_authorized_imports=["inspect", "json"]
)