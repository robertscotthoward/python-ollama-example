from lib.modelstack import *
from lib.vectordb import *


class Rag:
    def __init__(self, collection_name, corpus_folder, model_config):
        self.collection_name = collection_name
        self.corpus_folder = corpus_folder
        self.llm = ModelStack.from_config(model_config)
        self.rag = make_rag(collection_name, corpus_folder)

    def query(self, query):
        nResults =  int(self.llm.num_tokens() / (1000/5))
        context = self.rag.retrive_documents(query, n_results=nResults)
        prompt = f"""
QUERY: {query}

CONTEXT: {context}
        """
        answer = self.llm.query(prompt)
        return answer





if __name__ == "__main__":
    collection_name = "corpus1"
    corpus_folder = os.path.abspath(f"data/test/{collection_name}")
    config = {
        'class': 'ollama',
        'host': 'http://localhost:11434',
        'model': 'granite3.2:2b',
        'context-window': '128K'
    }
    rag = Rag(collection_name, corpus_folder, config)

    queries = [
        "I want to shift into another plane. What spell should I use?",
        "Who did Howard know?",
    ]
    for query in queries:
        print(f"Query: {query}")
        answer = rag.query(query)
        print(f"Answer: {answer}")
        print("-" * 80)


