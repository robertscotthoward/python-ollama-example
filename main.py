import yaml

from modelstack import ModelStack

with open("credentials.yaml", "r") as f:
    credentials = yaml.safe_load(f)

stack = credentials['modelstack']['bedrock-haiku']
modelstack = ModelStack.from_config(stack)

prompt = "What city was Benjamin Franklin born in?"

answer = modelstack.query(prompt)
print(answer)


