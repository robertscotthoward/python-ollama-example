import requests
import json
import yaml

with open("credentials.yaml", "r") as f:
    credentials = yaml.safe_load(f)

OLLAMA_HOST = credentials['ollama']['host']
model = 'codellama:7b-instruct'
prompt = """
You are a helpful programming assistant.
Write a Python function that takes a list of numbers and returns the list sorted in ascending order.
"""

r = requests.post(f'{OLLAMA_HOST}/api/generate', json={'model': model, 'prompt': prompt, 'stream': False})
answer = json.loads(r.text)['response']
print(answer)
