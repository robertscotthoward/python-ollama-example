import yaml
from lib.tools import *
from lib.modelstack import ModelStack


credentials = readYaml(findPath("credentials.yaml"))

stack = credentials['modelstack']['bedrock-haiku']
modelstack = ModelStack.from_config(stack)
prompt = "What city was Benjamin Franklin born in?"
answer = modelstack.query(prompt)
print(answer)
