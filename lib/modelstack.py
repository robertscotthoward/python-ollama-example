import time
import boto3
import requests
import json
import yaml
from lib.tools import *




class ModelStack:
    def __init__(self, config):
        self.config = config
        
    @staticmethod
    def from_config(config):
        cls = config.get('class')
        if cls == 'ollama':
            return OllamaModelStack(config)
        if cls == 'bedrock':
            return BedrockModelStack(config)
        raise ValueError(f"Unsupported model stack class: {cls}")
    
    def query(self, prompt):
        raise NotImplementedError("Subclasses must implement this method.")

    def query_yes_no(self, prompt):
        # Note: When debugging, this method may timeout in the debugger's expression evaluator
        # due to network calls to LLM APIs. Set PYDEVD_WARN_EVALUATION_TIMEOUT=10 or higher
        # in your environment to increase the debugger's evaluation timeout.
        prompt = "Only respond with 'yes' or 'no' or 'maybe' as the first word on its own line. If 'maybe', follow up with a short explanation.\n" + prompt
        answer = self.query(prompt, max_tokens=1024)
        word = answer.lower().strip().splitlines()[0].split(' .')[0]
        if word in ['yes', 'no']:
            return word
        return answer
    





class OllamaModelStack(ModelStack):
    def __init__(self, config):
        super().__init__(config)
        
    def query(self, prompt, max_tokens=1024):
        OLLAMA_HOST = self.config['host']
        model = self.config['model']
        max_tokens = from_metric(self.config.get('max_tokens', max_tokens))
        url = f'{OLLAMA_HOST}/api/generate'
        payload = {
            'model': model, 
            'prompt': prompt, 
            'stream': False, 
            'max_tokens': max_tokens
        }
        if 'temperature' in self.config:
            payload['temperature'] = self.config['temperature']
        if 'top_p' in self.config:
            payload['top_p'] = self.config['top_p']
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            raise Exception(f"Request failed with status code {r.status_code}: {r.text}")
        answer = json.loads(r.text)['response']
        return answer





class BedrockModelStack(ModelStack):
    def __init__(self, config):
        super().__init__(config)
        
    def query(self, prompt, max_tokens=1024):
        model = self.config['model']
        region = self.config.get('region', 'us-west-1')
        max_tokens = from_metric(self.config.get('max_tokens', max_tokens))
        temperature = self.config.get('temperature', 0.7)
        top_p = self.config.get('top_p', 1)

        params = {
            "anthropic_version": "bedrock-2023-05-31",  # For Anthropic models; omit for others
            "max_tokens": max_tokens,
            "messages": [  # Or use "prompt" for non-chat models like Llama
                {"role": "user", "content": prompt}
            ]
        }    
        
        # Can only be one of these.
        if temperature:
            params['temperature'] = temperature
        elif top_p:
            params['top_p'] = top_p
            
        body = json.dumps(params)
    
        client = boto3.client('bedrock-runtime', region_name=region)
        for i in range(3):
            try:
                response = client.invoke_model(
                    modelId=model,
                    body=body,
                    contentType='application/json',
                    accept='application/json'
                )
                break
            except Exception as e:
                print(f"Error invoking model: {e}")
                if isinstance(e, TimeoutError) or "timed out" in str(e).lower():
                    print("Request timed out. Consider increasing timeout or retrying.")
            if i > 0:
                time.sleep(1)
            
            
        # Parse the response body
        response_body = json.loads(response['body'].read())
    
        # Extract generated text (adjust based on model)
        if 'content' in response_body:  # For Anthropic-style
            answer = response_body['content'][0]['text']
        elif 'generation' in response_body:  # For Amazon Titan or others
            answer = response_body['generation']
        else:
            answer = response_body.get('text', 'No output found')
        
        return answer  # Or return full response_body for more details


class TEMPLATE_ModelStack(ModelStack):
    def __init__(self, config):
        super().__init__(config)
        
    def query(self, prompt):
        answer = "..."
        return answer




def test1():
    config = {
        'class': 'ollama',  
        'host':'http://localhost:11434',
        'model': 'tinyllama:1.1b'
    }
    modelstack = ModelStack.from_config(config)
    print(modelstack.query("What city was Benjamin Franklin born in?"))


def test2():
    config = {
        'class': 'bedrock',  
        'model': 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
        "temperature": 0.7,
        "region": "us-west-1"
    }
    modelstack = ModelStack.from_config(config)
    print(modelstack.query("What city was Benjamin Franklin born in?"))


if __name__ == "__main__":
    test1()
    test2()
