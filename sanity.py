# Scan all *.py files in this folder and find all the imports.
import os
import re
from pathlib import Path
from collections import defaultdict

def extract_imports_from_file(file_path):
    """Extract all import statements from a Python file."""
    imports = {
        'import': [],
        'from_import': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Handle standard imports: import module [as alias]
            if line.startswith('import '):
                # Remove 'import ' and any inline comments
                import_part = line[7:].split('#')[0].strip()
                # Handle multiple imports on one line
                modules = [m.strip() for m in import_part.split(',')]
                imports['import'].extend(modules)
            
            # Handle from imports: from module import something
            elif line.startswith('from ') and ' import ' in line:
                # Split on ' import ' to get module and what's imported
                parts = line.split(' import ', 1)
                module = parts[0][5:].strip()  # Remove 'from '
                items = parts[1].split('#')[0].strip()  # Remove inline comments
                imports['from_import'].append(f"from {module} import {items}")
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return imports

def scan_python_files(directory='.'):
    """Scan all Python files in the directory and subdirectories."""
    results = {}
    
    # Get all .py files
    root = os.path.abspath(directory)
    path = Path(directory)
    py_files = list(path.rglob('*.py'))
    # Skip __pycache__ and virtual environment directories
    py_files = [f for f in py_files if '__pycache__' not in str(f) and 'venv' not in str(f) and '.venv' not in str(f)]
    
    print(f"Found {len(py_files)} Python files\n")
    print("=" * 80)
    
    for py_file in sorted(py_files):
        relative_path = py_file.relative_to(path)
        imports = extract_imports_from_file(py_file)
        
        if imports['import'] or imports['from_import']:
            results[str(relative_path)] = imports
    
    return results

def print_results(results):
    """Pretty print the results."""
    for file_path, imports in results.items():
        print(f"\n📄 {file_path}")
        print("-" * 80)
        
        if imports['import']:
            print("  Standard imports:")
            for imp in sorted(set(imports['import'])):
                print(f"    • import {imp}")
        
        if imports['from_import']:
            print("  From imports:")
            for imp in sorted(set(imports['from_import'])):
                print(f"    • {imp}")

def collect_all_imports(results):
    """Collect all unique import statements."""
    all_imports = {
        'standard': set(),
        'from_imports': set()
    }
    
    for imports in results.values():
        for imp in imports['import']:
            all_imports['standard'].add(f"import {imp}")
        
        for imp in imports['from_import']:
            all_imports['from_imports'].add(imp)
    
    return all_imports



def modules():
    results = scan_python_files()
    seen = set()

    def f(x):
        if x.startswith('from '):
            x = x.split(' ')[1]
        if x in seen:
            return
        seen.add(x)
        return x

    for file_path, imports in results.items():
        dotted = []
        for imp in imports['import']:
            x = f(imp)
            if x:
                if '.' in x:
                    dotted.append(x)
                else:
                    yield x
        for imp in imports['from_import']:
            x = f(imp)
            if x:
                if '.' in x:
                    dotted.append(x)
                else:
                    yield x

    for d in dotted:
        yield d




def import_all():
    import time
    mm = sorted(modules())
    for m in mm:
        # if m in ['FlagEmbedding', 'langchain_text_splitters']:
        #     continue
        try:
            start = time.time()
            print(f"Importing {m} " + " " * (30 - len(m)), end="")
            __import__(m)
            module_time = time.time() - start
            print(f" {module_time:.4f}s")
        except Exception as e:
            print(f"ERROR: {e}")


def main1():
    print("🔍 Scanning Python files for imports...\n")
    
    results = scan_python_files()
    print_results(results)
    
    print("\n" + "=" * 80)
    print("\n📦 All unique import statements:")
    print("-" * 80)
    
    all_imports = collect_all_imports(results)
    
    if all_imports['standard']:
        print("\nStandard imports:")
        for i, imp in enumerate(sorted(all_imports['standard']), 1):
            print(f"{i:3}. {imp}")
    
    if all_imports['from_imports']:
        print("\nFrom imports:")
        start_num = len(all_imports['standard']) + 1
        for i, imp in enumerate(sorted(all_imports['from_imports']), start_num):
            print(f"{i:3}. {imp}")
    
    total_imports = len(all_imports['standard']) + len(all_imports['from_imports'])
    print(f"\n✨ Total unique import statements: {total_imports}")
    print(f"✨ Total files scanned: {len(results)}")


if __name__ == "__main__":
    import_all()