# This script will search through a folder of documents (corpus), 
# generate a vector database of the documents, 
# and submit a series of prompts to the vector database to answer questions about the resumes.
# It can also summarize each document or pull out specific information from the document.

# Cannot use these libraries. Too many compatibility issues.
# from unstructured.partition.auto import partition
# import textract
import os
from lib.tools import *
from lib.modelstack import ModelStack
from lib.rag import ChromaRAG
from chromadb.config import Settings



def list_resumes(self):
    """List all resumes in the database"""
    results = self.collection.get()
    return [metadata.get('filename') for metadata in results['metadatas']]

def run_job(self, job):
    system_prompt = job.get('system_prompt', '')
    files = job.get('files', {})
    folder = files.get('folder', '')
    extensions = files.get('extensions', [])
    exclude_patterns = files.get('exclude_patterns', [])
    target = files.get('target', '')
    prompts = job.get('prompts', [])

    if target.endswith('.yaml'):
        answers = readYaml(target)
    elif target.endswith('.json'):
        answers = readYaml(target)
    else:
        answers = []

    files_processed = set(answer.get('filepath') for answer in answers)

    if files:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(tuple(extensions)):
                    filepath = os.path.join(root, file)
                    if not filepath:
                        pass
                    if filepath in files_processed:
                        continue
                    filepath = filepath.replace('\\', '/')
                    if any(exclude_pattern in filepath for exclude_pattern in exclude_patterns):
                        continue

                    if any(answer.get('filepath') == filepath for answer in answers):
                        continue

                    text = read_corpus_document(filepath)
                    if not text:
                        continue

                    # answer = self.query_yes_no(f"Does the text below look like a resume, or describe a set of professional skills, or a professional knowledge base, or a personal study journal?\n\n{text}")
                    # if answer != 'yes':
                    #     answers.append({
                    #         'filepath': filepath,
                    #         'error': 'not a resume',
                    #         'reason': text
                    #     })
                    #     continue
                    
                    print(f"Processing {filepath}")
                    for prompt in prompts:
                        p = job.get('system_prompt', f'GIVEN:\n{{GIVEN}}\n\nPROMPT:\n{{PROMPT}}') + "\n\n"
                        p = p.replace('{{FILEPATH}}', filepath)
                        p = p.replace('{{GIVEN}}', text)
                        p = p.replace('{{PROMPT}}', prompt.get('prompt', ''))
                        p.strip()
                        if job.get('rag', None):
                            answer = self.query_rag(p)
                        else:
                            answer = self.query(p)
                        
                        if target.endswith('.yaml'):
                            answer = answer.split('```yaml', '')[1]
                            answer = answer.split('```', '')[0]
                            try:
                                o = yaml.safe_load(to_utf8(answer))
                            except Exception as e:
                                o = {
                                    'filepath': filepath,
                                    'error': str(e),
                                    'reason': answer
                                }
                                o['filepath'] = filepath
                                answers.append(o)
                                continue
                            o['filepath'] = filepath
                            answers.append(o)
                        elif target.endswith('.json'):
                            if '```json' in answer:
                                answer = answer.split('```json')[1]
                                answer = answer.split('```')[0]
                            o = json.loads(answer)
                            o['filepath'] = filepath
                            answers.append(o)
                        elif target.endswith(('.txt', '.md', '.rst')):
                            answer = answer.replace('```txt', '').replace('```', '')
                            o = answer.strip()
                            o = f"FILEPATH: {filepath}\n{o}"
                            answers.append(o)
                        else:
                            o = f"FILEPATH: {filepath}\n{o}"
                            answers.append(answer)


                        if target:
                            if target.endswith('.yaml'):
                                writeYaml(target, answers)
                            elif target.endswith('.json'):
                                writeJson(target, answers)
                            elif target.endswith('.txt'):
                                writeText(target, answers)
                            elif target.endswith('.md'):
                                writeText(target, answers)
                            elif target.endswith('.rst'):
                                writeText(target, answers)
                            else:
                                raise ValueError(f"Unsupported target file extension: {target}")
                            files_processed.add(filepath)
    return answers
                        






def summarize_resumes():
    """Example usage of the ChromaRAG system"""
    
    # Load credentials and model
    credentials = readYaml(findPath("credentials.yaml"))
    stack = credentials['modelstack']['bedrock-haiku']
    stack = credentials['modelstack']['ollama-summarization']
    stack = credentials['modelstack']['ollama-yaml-generation']
    modelstack = ModelStack.from_config(stack)
    jobfile = readYaml(findPath("jobs.yaml"))
    jobs = jobfile.get('jobs', {})
    job = jobs.get('resume', {})

    rag = ChromaRAG(modelstack, collection_name=job.get('rag', ''))
    rag.run_job(job)


def aggregate_resumes():
    """Process each resume in the summarized.yaml file"""
    target = readYaml(findPath("jobs.yaml"))['jobs']['resume']['files']['target']
    if not os.path.exists(target):
        print(f"Target file not found: {target}")
        return
    
    resumes = readYaml(target)
    
    agg = {
        'experience': {},
        'education': {},
        'skills': {},
        'certifications': {},
        'projects': {}
    }

    def agg_item(resume, agg, key, subkey, fields):
        agg[key] = agg.get(key, {})
        rr = resume.get(key) or []
        for r in rr:
            sk = r.get(subkey)
            if not sk:
                continue
            if type(sk) == list:
                continue
            agg[key][sk] = agg[key].get(sk) or {}
            for field in fields.split(','): 
                ft = ''
                if len(field.split(':')) > 1:
                    field, ft = field.split(':')
                if ft == 'str':
                    agg[key][sk][field] = agg[key][sk].get(field) or ""
                else:
                    agg[key][sk][field] = agg[key][sk].get(field) or {}
                v = r.get(field)
                if not v:
                    continue
                if type(v) == list:
                    for vItem in v:
                        if type(vItem) == dict:
                            for k, v in vItem.items():
                                agg[key][sk][field][k] = agg[key][sk][field].get(k) or {}
                                agg[key][sk][field][k][v] = None
                        else:
                            if ft == 'str':
                                agg[key][sk][field] += f"{vItem}\n"
                            else:
                                agg[key][sk][field][vItem] = None
                else:
                    if ft == 'str':
                        if not v in agg[key][sk][field]:
                            agg[key][sk][field] += f"{v}\n"
                    else:
                        agg[key][sk][field][v] = None
        return agg

    for resume in resumes:
        print(f"Processing resume: {resume.get('name', 'No name')}")
        agg_item(resume, agg, 'experience', 'company', 'dates,description:str,title')
        agg_item(resume, agg, 'education', 'school', 'dates,description,degree')
        agg_item(resume, agg, 'skills', 'skill', 'description,level,where_utilized,how_utilized,why_utilized,how_often_utilized,how_long_utilized,how_much_utilized')
        agg_item(resume, agg, 'certifications', 'certification', 'dates,description,issuer')
        agg_item(resume, agg, 'projects', 'project', 'dates,description,skills,technologies')

    writeYaml(target.replace('summarized', 'aggregated'), agg)


def condense_resumes():
    jobfile = readYaml(findPath("jobs.yaml"))
    jCondensed = jobfile.get('condensed')

    """Condense the resumes into a more readable format"""
    target = readYaml(findPath("jobs.yaml"))['jobs']['resume']['files']['target']
    if not os.path.exists(target):
        print(f"Target file not found: {target}")
        return

    aggFile = target.replace('summarized', 'aggregated')
    if not os.path.exists(aggFile):
        print(f"Aggregated file not found: {aggFile}")
        return
    agg = readYaml(aggFile)
    condenseFile = target.replace('summarized', 'condensed')

    credentials = readYaml(findPath("credentials.yaml"))
    stack = credentials['modelstack']['bedrock-haiku']
    stack = credentials['modelstack']['ollama-yaml-generation']
    stack = credentials['modelstack']['ollama-summarization']
    modelstack = ModelStack.from_config(stack)
    rag = ChromaRAG(modelstack, collection_name=None)

    out = {}
    for k0, v0 in agg.items():
        out[k0] = {}
        for k1, v1 in v0.items():
            prompt = jCondensed.get(k0).replace('{KEY}', k1).replace('{JSON}', json.dumps(v1))
            result = rag.query(prompt, max_tokens="8K")
            result = result.replace('```yaml', '').replace('```json', '').replace('```', '')
            try:
                o = json.loads(result)
            except Exception as e:
                try:
                    o = yaml.safe_load(to_utf8(result))
                except Exception as e:
                    o = {
                        'error': str(e),
                        'reason': result
                    }
                    continue
            out[k0][k1] = o
            writeYaml(condenseFile, out)


def summarize_python_codebase():
    """Example usage of the ChromaRAG system"""
    
    # Load credentials and model
    credentials = readYaml(findPath("credentials.yaml"))
    stack = credentials['modelstack']['bedrock-haiku']
    stack = credentials['modelstack']['ollama-summarization']
    stack = credentials['modelstack']['ollama-code']
    stack = credentials['modelstack']['bedrock-claude-connet-4-5']
    modelstack = ModelStack.from_config(stack)
    jobfile = readYaml(findPath("jobs.yaml"))
    jobs = jobfile.get('jobs', {})
    job = jobs.get('python-zinclusive', {})

    rag = ChromaRAG(modelstack, collection_name=job.get('rag', ''))
    rag.run_job(job)


def test2():    
    credentials = readYaml(findPath("credentials.yaml"))
    stack = credentials['modelstack']['bedrock-haiku']
    modelstack = ModelStack.from_config(stack)
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
    #summarize_resumes()
    # aggregate_resumes()
    # condense_resumes()
    summarize_python_codebase()
