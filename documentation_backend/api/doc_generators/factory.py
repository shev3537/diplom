from .language_detector import detect_language
from .python_generator import PythonDocGenerator
from .cpp_generator import CppDocGenerator

def get_generator(repo_path: str):
    lang = detect_language(repo_path)
    if lang == 'python':
        return PythonDocGenerator()
    elif lang == 'cpp' or lang == 'c' :
        return CppDocGenerator()
    else:
        raise ValueError(f"Unsupported language: {lang}")
