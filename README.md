# Hello World Agent with MCP

A simple demonstration of Tiny Agents using Gradio MCP server and local Ollama.

## What this does

This example creates:
- **Gradio MCP Server**: A simple server that provides a "hello world" function
- **Tiny Agent**: An agent that connects to your local Ollama endpoint and can use the MCP server's tools

## Prerequisites

1. **Ollama** running locally at `http://127.0.0.1:11434`
2. **qwen3:0.6b** model installed in Ollama
3. **Node.js and npm** for MCP remote connectivity

## Setup

### 1. Install Ollama and the model
```bash
# If you haven't already, install Ollama
# Then pull the model:
ollama pull qwen3:0.6b
```

### 2. Install Node.js dependencies
```bash
# Install mcp-remote globally
npm install -g mcp-remote
```

### 3. Install Python dependencies
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

## Usage

### 1. Start Ollama
Make sure Ollama is running:
```bash
ollama serve
```

### 2. Run the agent
```bash
# Using uv
uv run python main.py

# Or using python directly
python main.py
```

### 3. Interact with the agent
Once started, you can:
- Type messages to chat with the agent
- Ask it to use the hello world function (e.g., "Can you greet Alice using your tool?")
- Type 'quit' to exit

## Example Interaction

```
🎉 Agent is ready! Type 'quit' to exit.
==================================================

👤 You: Can you greet Alice using your available tools?

🤖 Agent: I'll use the hello world function to greet Alice for you.

*Agent calls the hello_world_function with name="Alice"*

Hello, Alice! This message comes from the MCP server.
```

## How it works

1. **Gradio MCP Server**: Creates an MCP-enabled Gradio interface at `http://127.0.0.1:7860`
2. **MCP Protocol**: The server exposes the `hello_world_function` via MCP
3. **Tiny Agent**: Connects to both Ollama (for LLM) and the Gradio server (for tools)
4. **Tool Usage**: The agent can discover and use the hello world function when appropriate

## Troubleshooting

- **"Connection refused"**: Make sure Ollama is running (`ollama serve`)
- **"Model not found"**: Install the model (`ollama pull qwen3:0.6b`)
- **"mcp-remote not found"**: Install it with `npm install -g mcp-remote`
- **Port conflicts**: The Gradio server uses port 7860 by default
