# Overview
Here is a very short python example to query an Ollama LLM with a prompt.
You can install Ollama on your local machine and run `ollama pull `


# Setup

* Clone this repo.
* Change to the local folder.
* Open command prompt.
* Ensure you have uv installed on your machine by running `uv --version`. Else `scoop install uv`
* Run `reset-venv.bat`
* Create a local file called `credentials.yaml`.
* Put in that file:
```yaml
ollama:
  host: SERVER-URL
```
* Replace the "SERVER-URL" value with your actual server. Could be:
  * `http://localhost:443/v1` to hit your local server if you are running it there.
  * `https://YOUR-SPECIFIC-NAME.ngrok-free.dev:443/v1` if you are running an ngrok end point on another machine.

# Usage

```dos
python main.py
```

# Configure Visual Code

To use Ollama in Visual Code, perhaps to avoid token charges for Cursor and Copilot, follow these steps:

* Start VS Code
* Install the extension: "[Continue - open-source AI code agent](https://marketplace.visualstudio.com/items?itemName=Continue.continue)"
* Open this file: `%USERPROFILE%\.continue\config.yaml` and pick one of these configurations:

## Local Ollama Server
```yaml
version: 1.0.0
schema: v1
models:
  - title: CodeLlama 7b Instruct
    provider: ollama
    model: codellama:7b-instruct
    roles:
      - chat
      - edit
      - apply
  - title: CodeLlama 7b Instruct
    provider: ollama
    model: codellama:7b-instruct
    roles:
      - autocomplete
  - title: Nomic Embed
    provider: ollama
    model: nomic-embed-text
    roles:
      - embed
```

## Remote Ollama Server
```yaml
version: 1.0.0
schema: v1

name: My Local Ollama Config
model: "CodeLlama 7b Instruct"

models:
  - name: "CodeLlama 7b Instruct"
    provider: ollama
    model: codellama:7b-instruct
    apiBase: https://YOUR-SPECIFIC-NAME.ngrok-free.dev
    roles:
      - chat
      - edit
      - apply

  - name: "CodeLlama 7b Autocomplete"
    provider: ollama
    model: starcoder2:3b
    apiBase: https://YOUR-SPECIFIC-NAME.ngrok-free.dev
    roles:
      - autocomplete

```

# Troubleshooting

I get this error in VS Code:

Error loading Local Config. Chat is disabled until a model is available.



But this works:

set OLLAMA_HOST=https://YOUR-SPECIFIC-NAME.ngrok-free.dev:443/v1

ollama run codellama:7b-instruct "Tell me about Moscow."
