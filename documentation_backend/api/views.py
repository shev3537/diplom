import os
import tempfile
import shutil
import stat
import time
import ast
import markdown2
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from git import Repo

class UploadRepoUrlView(APIView):
    def post(self, request, format=None):
        repo_url = request.data.get('repo_url')
        if not repo_url:
            return Response({'error': 'No repo_url provided'}, status=status.HTTP_400_BAD_REQUEST)

        temp_dir = tempfile.mkdtemp()
        repo = None
        try:
            # Клонируем репозиторий
            repo = Repo.clone_from(repo_url, temp_dir)
            docs = analyze_code(temp_dir)
            docs['readme'] = parse_readme(temp_dir)
            docs['commits'] = get_commits(repo)
        except Exception as e:
            safe_rmtree(temp_dir)
            return Response({'error': str(e)}, status=400)
        # Явно закрываем репозиторий (важно для Windows!)
        if repo is not None and hasattr(repo, 'close'):
            repo.close()
        time.sleep(0.5)  # Даем системе отпустить файлы
        safe_rmtree(temp_dir)
        return Response(docs, status=200)

def safe_rmtree(path):
    """Безопасно удаляет папку даже если есть защищённые файлы (Windows)."""
    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if os.path.exists(path):
        shutil.rmtree(path, onerror=remove_readonly)

def parse_readme(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower() == "readme.md":
                with open(os.path.join(root, file), encoding='utf-8') as f:
                    content = f.read()
                html = markdown2.markdown(content)
                return {'filename': file, 'content': html}
    return None

def extract_docstrings(file_path):
    with open(file_path, encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    result = {
        'module_docstring': ast.get_docstring(tree),
        'classes': [],
        'functions': [],
        'api_endpoints': []
    }
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            result['classes'].append({
                'name': node.name,
                'docstring': ast.get_docstring(node)
            })
        elif isinstance(node, ast.FunctionDef):
            result['functions'].append({
                'name': node.name,
                'docstring': ast.get_docstring(node)
            })
            # API endpoints
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr'):
                    if decorator.func.attr in ['route', 'get', 'post', 'put', 'delete']:
                        result['api_endpoints'].append({
                            'function': node.name,
                            'decorator': decorator.func.attr,
                            'path': decorator.args[0].s if decorator.args else ''
                        })
    return result

def analyze_code(path):
    docs = {'files': []}
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    doc_info = extract_docstrings(file_path)
                    docs['files'].append({
                        'name': os.path.relpath(file_path, path),
                        **doc_info
                    })
                except Exception:
                    continue
    return docs

def get_commits(repo, max_count=10):
    commits = []
    branch = repo.head.reference.name if repo.head.is_valid() else 'master'
    for commit in list(repo.iter_commits(branch, max_count=max_count)):
        commits.append({
            'hexsha': commit.hexsha,
            'author': commit.author.name,
            'date': commit.committed_datetime.strftime('%Y-%m-%d %H:%M'),
            'message': commit.message.strip()
        })
    return commits
