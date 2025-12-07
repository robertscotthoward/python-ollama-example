import os
from lib.fileconvert import convert_all_doc_to_docx, docx_to_text
from lib.tools import *
import pypdf


file_extensions = [".docx", ".pdf", ".txt", ".md", ".rst"]


def get_text(filepath):
    if filepath.endswith(".pdf"):
        return pypdf.PdfReader(filepath).pages[0].extract_text()
    elif filepath.endswith(".docx"):
        return docx_to_text(filepath)
    else:
        return readText(filepath)


class Corpus:
    """Class for enumerating a corpus of documents and getting the text of the documents."""
    

    def __init__(self, file_extensions=file_extensions):
        self.file_extensions = file_extensions


    def enumerate_files(self, corpus_folder):
        """Load corpus from a folder into the vector database"""
        if not os.path.exists(corpus_folder):
            raise ValueError(f"Corpus folder not found: {corpus_folder}")

        for root, dirs, files in os.walk(corpus_folder):
            for file in files:
                if file.endswith(tuple(self.file_extensions)):
                    filepath = os.path.join(root, file)
                    filepath = filepath.replace('\\', '/')
                    yield filepath


    def get_text(self, filepath):
        return get_text(filepath)


    def convert_files(self, corpus_folder):
        convert_all_doc_to_docx(corpus_folder)


