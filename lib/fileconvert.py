import subprocess
import os
from docx import Document
from lib.tools import readText

def convert_doc_to_docx(doc_path):
    """
    Converts a .doc file directly to plain text (.txt) using Pandoc.
    Requires Pandoc to be installed and in the system's PATH.
    """
    if not os.path.exists(doc_path):
        print(f"Error: Source file not found at '{doc_path}'")
        return None
        
    output_dir = os.path.dirname(doc_path)
    base_name = os.path.splitext(os.path.basename(doc_path))[0]
    temp_txt_path = os.path.join(output_dir, f"{base_name}.docx")
    
    if not os.path.exists(temp_txt_path):
        try:
            print(f"Converting '{doc_path}' to text using Pandoc...")
            subprocess.run([
                r"C:\Program Files\Microsoft Office\root\Office16\Wordconv.exe",
                "-oice",
                "-nme",
                doc_path,
                temp_txt_path
            ], check=True, cwd=output_dir, capture_output=True)

            # Read the content from the newly created text file
            with open(temp_txt_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
            
            print("✅ Successfully extracted text using Pandoc.")
            return full_text
            
        except FileNotFoundError:
            print("❌ CONVERSION FAILED: 'pandoc' command not found. Ensure Pandoc is installed.")
            return None
        except subprocess.CalledProcessError as e:
            print(f"❌ CONVERSION FAILED: Pandoc error. Output: {e.stderr.decode()}")
            return None


    document = Document(temp_txt_path)
    text = '\n\n'.join(p.text for p in document.paragraphs)
    return text

if __name__ == "__main__":
    doc_file = r"C:\Rob\RAG\Resumes, Work History, Career\2006\2003-04-23.doc"
    extracted_text = convert_doc_to_docx(doc_file)
    print(extracted_text)
