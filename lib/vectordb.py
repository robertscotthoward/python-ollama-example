import os
import datetime
from lib.splitter import *
from lib.tools import *
from lib.corpus import *
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



class VectorDb:
    def __init__(self, corpus, splitter, collection_name):
        self.collection_name = collection_name
        self.corpus = corpus
        self.splitter = splitter

    def add_chunk(self, chunk, filepath, chunk_index):
        if not hasattr(self, 'chunk_batch') or not self.chunk_batch:
            self.chunk_batch = {
                'chunks': [],
                'metadatas': [],
                'ids': []
            }
        self.chunk_batch['chunks'].append(chunk)
        self.chunk_batch['metadatas'].append({"filename": filepath, "chunk_index": chunk_index})
        self.chunk_batch['ids'].append(f"{filepath}#{chunk_index}")


    def add_document(self, filepath):
        text = self.corpus.get_text(filepath)
        chunks = self.splitter.get_chunks(text)
        for chunk_index, chunk in enumerate(chunks):
            self.add_chunk(chunk, filepath, chunk_index)
        self.commit_batch(threshold=100)


    def commit_batch(self, threshold=0):
        raise NotImplementedError("Subclasses must implement this method.")


    def load_corpus(self, corpus_folder, last_updated=0):
        """
        Load corpus from a folder into the vector database
        @corpus_folder is the folder to load the corpus from.
        @last_updated is the minimum last updated time of the files in the corpus to load. All other files will be skipped.
        @return the maximum last updated time of the files in the corpus.
        """

        # Pre-scan the corpus to find the maximum last updated time
        m = 0
        for filepath in self.corpus.enumerate_files(corpus_folder):
            file_updated = os.path.getmtime(filepath)
            if file_updated > m:
                m = file_updated
        sMaxUpdate = datetime.datetime.fromtimestamp(m).isoformat()

        max_updated = 0
        for filepath in self.corpus.enumerate_files(corpus_folder):
            file_updated = os.path.getmtime(filepath)
            if file_updated > max_updated:
                max_updated = file_updated
            if file_updated > last_updated:
                self.add_document(filepath)

        self.commit_batch()
        return max_updated

    def get_reranker(self):
        if hasattr(self, 'reranker') and self.reranker:
            return self.reranker
        import torch
        from FlagEmbedding import FlagReranker
        if torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        modelName = 'BAAI/bge-reranker-v2-m3'
        if self.device == "cuda":
            modelName = 'BAAI/bge-reranker-large'
        self.reranker = FlagReranker(modelName, device=self.device, use_fp16=True)
        return self.reranker




class ChromaVectorDb(VectorDb):
    """RAG system for querying a corpus using ChromaDB vector database"""
    
    def __init__(self, corpus, splitter, collection_path=None):
        super().__init__(corpus, splitter, collection_path)
        
        self.collection_path = os.path.abspath(collection_path)
        self.collection_dir = os.path.dirname(collection_path)
        self.collection_name = os.path.basename(collection_path)
        self.client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            is_persistent=True,
            persist_directory=self.collection_dir
        ))
        
        # Get or create the collection
        if self.collection_name:
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            if self.collection.count():
                print(f"Collection {self.collection_name} loaded with {self.collection.count()} entries.")
            else:
                print(f"Collection {self.collection_name} created.")
    
    
    def commit_batch(self, threshold=0):
        if hasattr(self, 'chunk_batch') and self.chunk_batch and len(self.chunk_batch['chunks']) >= threshold:
            self.collection.add(
                documents=self.chunk_batch['chunks'],
                metadatas=self.chunk_batch['metadatas'],
                ids=self.chunk_batch['ids']
            )
            self.chunk_batch = None




    def retrive_documents(self, query, n_results=80):
        """Query the vector database and generate an answer using the LLM"""
        
        numEntries = self.collection.count()

        # Retrieve a generous amount of relevant documents (cheap and fast)
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant documents found."
        
        # Re-rank them with a cross-encoder
        reranker = self.get_reranker()

        def rerank_with_bge(query: str, documents, top_k: int = 12):
            pairs = [[query, doc] for doc in documents]
            scores = reranker.compute_score(pairs, batch_size=32)
            # scores is a list of floats
            ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
            return [doc for doc, score in ranked[:top_k]]

        # Usage
        raw_results = self.collection.query(query_texts=[query], n_results=80)['documents'][0]
        top_reranked = rerank_with_bge(query, raw_results, top_k=12)        

        results['documents'][0] = top_reranked
        results['metadatas'][0] = [metadata for metadata in results['metadatas'][0]]


        # Build context from retrieved documents
        context_parts = []
        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
            filename = metadata.get('filename', 'Unknown')
            context_parts.append(f"From {filename}:\n{doc}\n")
        
        context = "\n---\n".join(context_parts)
        
        return context



def make_rag(collection_name, corpus_folder):
    corpus = Corpus()
    corpus.convert_files(corpus_folder)

    splitter = RecursiveCharacterText_Splitter(chunk_size=1000, chunk_overlap=200)
    rag = ChromaVectorDb(corpus, splitter, collection_path=f"data/chroma_db/{collection_name}")

    cache = get_cache("chroma_rag.json")
    collections = cache.get("collections", {})
    collection = collections.get(collection_name, {})
    last_updated = collection.get("last_updated", 0)
    last_updated = rag.load_corpus(corpus_folder, last_updated)
    collection["last_updated"] = last_updated
    put_cache("chroma_rag.json", cache)
    return rag


if __name__ == "__main__":
    collection_name = "corpus1"
    corpus_folder = os.path.abspath(f"data/test/{collection_name}")
    rag = make_rag(collection_name, corpus_folder)

    context = rag.retrive_documents("I want to shift into another plane. What spell should I use?")
    print(context)
