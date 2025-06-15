import os

def detect_language(repo_path: str) -> str:
    counts = {'python': 0, 'c': 0, 'cpp': 0}
    
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            # Python detection
            if file.endswith('.py'):
                counts['python'] += 1
            if file in ['setup.py', 'requirements.txt']:
                counts['python'] += 100
                
            # C detection
            if file.endswith(('.c', '.h')):
                counts['c'] += 1
                
            # C++ detection
            if file.endswith(('.cpp', '.hpp', '.cc', '.cxx', '.hxx', '.hh')):
                counts['cpp'] += 1
                
    lang = max(counts, key=counts.get)
    if counts[lang] == 0:
        return 'unknown'
    # Prioritize C++ over C when both present
    if lang == 'c' and counts['cpp'] > 0:
        return 'cpp'
    return lang