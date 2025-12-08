


```mermaid
graph LR
RAG --> VDB
RAG --> Splitter
RAG --> Corpus
RAG --> ModelStack
ModelStack -.-> OllamaModelStack
ModelStack -.-> BedrockModelStack
```