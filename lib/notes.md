


```mermaid
graph LR
RAG --> VDB
RAG --> Chunker
RAG --> Corpus
RAG --> ModelStack
ModelStack -.-> OllamaModelStack
ModelStack -.-> BedrockModelStack
```