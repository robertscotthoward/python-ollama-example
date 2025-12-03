import subprocess
import os
from docx import Document
from lib.tools import readText


def convert_all_doc_to_docx(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".doc"):
                convert_doc_to_docx(os.path.join(root, file))


def convert_doc_to_docx(doc_path):
    if not os.path.exists(doc_path):
        print(f"Error: Source file not found at '{doc_path}'")
        return None
        
    output_dir = os.path.dirname(doc_path)
    base_name = os.path.splitext(os.path.basename(doc_path))[0]
    docx_path = os.path.join(output_dir, f"{base_name}.docx")
    
    # if os.path.exists(docx_path):
    #     # Set the last updated time to the doc file
    #     os.utime(docx_path, (os.path.getatime(doc_path), os.path.getmtime(doc_path)))

    if not os.path.exists(docx_path):
        try:
            print(f"Converting '{doc_path}' to text using docx...")
            subprocess.run([
                r"C:\Program Files\Microsoft Office\root\Office16\Wordconv.exe",
                "-oice",
                "-nme",
                doc_path,
                docx_path
            ], check=True, cwd=output_dir, capture_output=True)

            # Set the last updated time to the docx file
            os.utime(docx_path, (os.path.getatime(doc_path), os.path.getmtime(doc_path)))
           
        except FileNotFoundError:
            print("❌ CONVERSION FAILED: 'pandoc' command not found. Ensure Pandoc is installed.")
            return None
        except subprocess.CalledProcessError as e:
            print(f"❌ CONVERSION FAILED: Pandoc error. Output: {e.stderr.decode()}")
            return None


def docx_to_text(docx_path):
    document = Document(docx_path)
    text = '\n\n'.join(p.text for p in document.paragraphs)
    return text


if __name__ == "__main__":
    doc_file = r"C:\Rob\RAG\Resumes, Work History, Career\2006\2003-04-23.doc"
    extracted_text = convert_doc_to_docx(doc_file)
    print(extracted_text)
