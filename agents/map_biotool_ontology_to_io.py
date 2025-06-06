from smolagents import CodeAgent, LiteLLMModel

model = LiteLLMModel(
    # model_id="ollama/devstral:latest",
    model_id="ollama/qwen3:0.6b",
    api_base="http://localhost:11434",
    temperature=0.0,
    max_tokens=5000,
)

tool_list = []

agent = CodeAgent(
    tools=tool_list,
    model=model,
    additional_authorized_imports=["inspect", "json"]
)