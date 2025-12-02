# This script will search through a folder of resumes, generate a vector database of the resumes, and submit a series of prompts to the vector database to answer questions about the resumes.

# Cannot use these libraries. Too many compatibility issues.
# from unstructured.partition.auto import partition
# import textract
import os
from lib.tools import *
from lib.modelstack import ModelStack
import pdfminer
import docx2txt 
import chromadb
from chromadb.config import Settings


def read_corpus_document(filepath):
    if filepath.endswith(".pdf"):
        return pdfminer.six.extract_text(filepath)
    elif filepath.endswith(".docx"):
        return docx2txt.process(filepath)
    elif filepath.endswith(".doc"):
        return docx2txt.process(filepath)
    else:
        return readText(filepath)


class ChromaRAG:
    """RAG system for querying a corpus using ChromaDB vector database"""
    
    def __init__(self, modelstack, collection_name="MyNewCollection", file_extensions="doc,docx,pdf,txt,md,rst"):
        self.modelstack = modelstack
        self.collection_name = collection_name
        self.file_extensions = file_extensions.split(",")
        self.client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            is_persistent=True,
            persist_directory="./chroma_db"
        ))
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

        self.state = get_cache(f"chroma_rag") or {}
        self.state['collections'] = self.state.get("collections", {})
        self.state['collections'][self.collection_name] = self.state['collections'].get(self.collection_name, {})
        put_cache(f"chroma_rag", self.state)

    def load_corpus(self, corpus_folder):
        """Load corpus from a folder into the vector database"""
        if not os.path.exists(corpus_folder):
            raise ValueError(f"Corpus folder not found: {corpus_folder}")
        
        before = self.state['collections'][self.collection_name].get("last_updated", 0)
        max_updated = 0
        for root, dirs, files in os.walk(corpus_folder):
            for file in files:
                if file.endswith(tuple(self.file_extensions)):
                    filepath = os.path.join(root, file)
                    last_updated = os.path.getmtime(filepath)
                    if last_updated > before:
                        print(f"Adding {file} to the vector database")
                        max_updated = max(max_updated, last_updated)
                        text = read_corpus_document(filepath)
                        self.collection.add(
                            documents=[text],
                            metadatas=[{"filename": file, "last_updated": last_updated}],
                            ids=[file]
                        )
        # Update the state with the latest timestamp
        if max_updated > 0:
            self.state['collections'][self.collection_name]['last_updated'] = max_updated
            self.state['collections'][self.collection_name]['folder'] = corpus_folder
            put_cache(f"chroma_rag", self.state)
        
        return len(self.collection.get())
    
    def add_document(self, document):
        """Add a document to the vector database"""
        self.collection.add(
            documents=[document],
            metadatas=[{"filename": document.filename}],
            ids=[document.id]
        )
    
    def query(self, question, n_results=3):
        """Query the vector database and generate an answer using the LLM"""
        
        # Retrieve relevant documents
        results = self.collection.query(
            query_texts=[question],
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
        
        # Create prompt with context
        prompt = f"""Based on the following resume excerpts, answer this question: {question}

Context from resumes:
{context}

Answer:"""
        
        # Get answer from LLM
        answer = self.modelstack.query(prompt)
        
        return {
            'answer': answer,
            'sources': [m.get('filename') for m in results['metadatas'][0]],
            'num_sources': len(results['documents'][0])
        }
    
    def list_resumes(self):
        """List all resumes in the database"""
        results = self.collection.get()
        return [metadata.get('filename') for metadata in results['metadatas']]


def test1():
    """Example usage of the ChromaRAG system"""
    
    # Load credentials and model
    credentials = readYaml(findPath("credentials.yaml"))
    stack = credentials['modelstack']['bedrock-haiku']
    modelstack = ModelStack.from_config(stack)
    
    # Initialize RAG system
    rag = ChromaRAG(modelstack, collection_name="resumes")
    
    # Load resumes (you'll need to create a 'resumes' folder with .txt or .md files)
    corpus_folder = r"C:\Rob\RAG\Resumes, Work History, Career"
    if os.path.exists(corpus_folder):
        rag.load_corpus(corpus_folder)
    else:
        print(f"Creating {corpus_folder} folder. Please add corpus files to this folder.")
        os.makedirs(corpus_folder, exist_ok=True)
        print("No resumes loaded. Add files and run again.")
        return
    
    # Example queries
    questions = [
        "What programming languages do candidates know?",
        "Who has experience with Python?",
        "What are the most common skills across all resumes?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        result = rag.query(question, n_results=3)
        print(f"Answer: {result['answer']}")
        print(f"Sources: {', '.join(result['sources'])}")
        print("-" * 80)


if __name__ == "__main__":
    test1()
