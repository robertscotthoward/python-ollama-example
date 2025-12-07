import os
from lib.tools import *
from lib.corpus import Corpus
import chromadb
from chromadb.config import Settings


file_extensions = [".docx", ".pdf", ".txt", ".md", ".rst"]


def read_corpus_document(filepath):
    if filepath.endswith(".pdf"):
        return pypdf.PdfReader(filepath).pages[0].extract_text()
    elif filepath.endswith(".docx"):
        return docx_to_text(filepath)
    else:
        return readText(filepath)



class RAG:

    def __init__(self, corpus, collection_name="MyNewCollection"):
        self.collection_name = collection_name
        self.corpus = corpus

    def load_corpus(self):
        for filepath in self.corpus.enumerate_files():
            text = self.corpus.get_text(filepath)
            self.add_document(text, filepath)
            self.collection.add(
                documents=[text],
                metadatas=[{"filename": filepath}],
                ids=[filepath]
            )

    def add_document(self, text, filepath):
        raise NotImplementedError("Subclasses must implement this method.")


class ChromaRAG(RAG):
    """RAG system for querying a corpus using ChromaDB vector database"""
    
    def __init__(self, corpus, collection_name="MyNewCollection"):
        super().__init__(corpus, collection_name)
        
        self.client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            is_persistent=True,
            persist_directory="./chroma_db"
        ))
        
        # Get or create the collection
        if self.collection_name:
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
    
    
    def add_document(self, text, filepath):
        self.collection.add(
            documents=[text],
            metadatas=[{"filename": filepath}],
            ids=[filepath]
        )


    def load_corpus(self, corpus_folder, cache={}):
        """
        Load corpus from a folder into the vector database
        @cache is a dictionary of the form {filepath: last_updated}
        """
        
        max_updated = 0
        for filepath in self.corpus.enumerate_files(corpus_folder):
            last_updated = cache.get(filepath, 0)
            if last_updated > max_updated:
                max_updated = last_updated
            text = self.corpus.get_text(filepath)
            self.add_document(text, filepath)
    

    def retrive_documents(self, prompt, n_results=10):
        """Query the vector database and generate an answer using the LLM"""
        
        # Retrieve relevant documents
        results = self.collection.query(
            query_texts=[prompt],
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant documents found."
        
        # Build context from retrieved documents
        context_parts = []
        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
            filename = metadata.get('filename', 'Unknown')
            context_parts.append(f"From {filename}:\n{doc}\n")
        
        context = "\n---\n".join(context_parts)
        
        return context
    

if __name__ == "__main__":
    corpus_folder = os.path.abspath(r"data/test/corpus1")
    corpus = Corpus()
    corpus.convert_files(corpus_folder)

    rag = ChromaRAG(corpus)
    rag.load_corpus(corpus_folder)

    context = rag.retrive_documents("I want to shift into another plane. What spell should I use?")
    print(context)
