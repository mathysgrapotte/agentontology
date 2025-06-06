# AgentOntology



Our agent `AgentOntology` is a helper agent to find file ontologies.

## Demo

You can watch a demo video in [this URL](https://www.loom.com/share/2929a2b8b976438d81f5885b6df0a992).

## The team

- Cristina Araiz Sancho 
    - <img src="https://github.com/favicon.ico" width="16" height="16" alt="GitHub"/> @caraiz2001 
    - <img src="https://huggingface.co/favicon.ico" width="16" height="16" alt="HuggingFace"/> @caraiz2001
- Júlia Mir Pedrol 
    - <img src="https://github.com/favicon.ico" width="16" height="16" alt="GitHub"/> @mirpedrol 
    - <img src="https://huggingface.co/favicon.ico" width="16" height="16" alt="HuggingFace"/> @asthara
- Mathys Grapotte 
    - <img src="https://github.com/favicon.ico" width="16" height="16" alt="GitHub"/> @mathysgrapotte 
    - <img src="https://huggingface.co/favicon.ico" width="16" height="16" alt="HuggingFace"/> @mgrapotte
- Suzanne Jin 
    - <img src="https://github.com/favicon.ico" width="16" height="16" alt="GitHub"/> @suzannejin 
    - <img src="https://huggingface.co/favicon.ico" width="16" height="16" alt="HuggingFace"/> @suzannejin

## Background

We are contributing to the [nf-core](https://nf-co.re/) community by developing a Gradio app powered by an AI agent. 
This app simplifies the annotation of nf-core module input and output files by automatically assigning standardized EDAM ontology terms.

nf-core is a vibrant community dedicated to curating best-practice analysis pipelines built using [Nextflow](https://www.nextflow.io/), a powerful workflow management system. 

Central to nf-core's success is its commitment to standardization, enabling easy reuse of modules - wrappers around bioinformatics tools - and streamlined contributions across multiple projects.

Accurate and thorough annotation of modules is essential to achieve this standardization, but manual annotation can be tedious. Here's where our tool enters the game! EDAM ontology provides clear, standardized labels, making bioinformatics data easily understandable and interoperable.

Benefits of tagging input/output files with EDAM ontology:
- Improved clarity
- Enhanced interoperability
- Better discoverability
- FAIR compliance
- Automation-ready

## Prerequisites

1. **Ollama** running locally at `http://127.0.0.1:11434`
2. **devstral:latest** model installed in Ollama
3. **uv** to manage dependencies

## Setup

### 1. Install Ollama and pull the model
```bash
# If you haven't already, install Ollama
# Then pull the model:
ollama pull devstral:latest
```

### 3. Install Python dependencies
```bash
uv sync
```

## Usage

### 1. Start Ollama
```bash
ollama serve
```

### 2. Run the agent
```bash
python main.py
```

### 3. Interact with the agent

Once started, open `http://127.0.0.1:11434` in your browser to see the Gradio app interface.
You will see a textbox to provide the name of the module you want to update.
Wait for the agent to do its job!

## How it works

We have implemented a pipeline using Python funcitons and calling AI agents when needed.

1. We pull the `meta.yml` file from the requested nf-core module (this file contains the module metadata.) ➡️ [Python funciton]
2. We ask the agent to retrieve the ontology terms from the EDAM database, and select the relevant term for each input and output file. ➡️ [`CodeAgent` with a `LiteLLMModel`]
3. We return the ontology terms and the updated `meta.yml` file. ➡️ [Python funciton]

