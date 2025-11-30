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
  * `http://localhost:11434` to hit your local server if you are running it there.
  * `https://YOUR-SPECIFIC-NAME.ngrok-free.dev:443` if you are running an ngrok end point on another machine.

# Usage

```
python main..py
```
