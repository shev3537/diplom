# api/doc_generators/python_generator.py
import os
import shutil
import subprocess
import tempfile
import stat
from pathlib import Path
from typing import Optional
from .base import DocGenerator

def remove_readonly(func, path: str, _) -> None:
    """Remove readonly attribute to allow file deletion on Windows"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def find_root_package(repo_path: str) -> Optional[str]:
    """
    Find the top-level Python package directory with __init__.py
    that contains the most Python files.
    """
    root_package = None
    max_files = 0
    
    for root, dirs, files in os.walk(repo_path):
        # Skip virtual environments and hidden directories
        if any(part.startswith('.') or part == '__pycache__' 
               for part in Path(root).relative_to(repo_path).parts):
            continue
        
        # Check for Python package
        if '__init__.py' in files:
            py_files = sum(1 for f in files if f.endswith('.py'))
            
            # Prefer package closest to repo root
            depth = len(Path(root).relative_to(repo_path).parts)
            weight = py_files * (10 / (depth + 1))
            
            if weight > max_files:
                max_files = weight
                root_package = root
    
    return root_package

class PythonDocGenerator(DocGenerator):
    def generate(self, repo_path: str, repo_name: str) -> str:
        # Create temporary working directories
        with tempfile.TemporaryDirectory() as tmp_rst_dir:
            html_output_dir = os.path.join(repo_path, 'docs_html')
            
            # Clean existing output
            if os.path.exists(html_output_dir):
                shutil.rmtree(html_output_dir, onerror=remove_readonly)
            
            # Locate main package
            src_dir = find_root_package(repo_path)
            if not src_dir:
                raise RuntimeError("No valid Python package found")
            
            # Run sphinx-apidoc
            proc_apidoc = subprocess.run([
                'sphinx-apidoc',
                '-o', tmp_rst_dir,
                src_dir,
                '--force',
                '--module-first',
                '--separate'
            ], capture_output=True, text=True)
            
            if proc_apidoc.returncode != 0:
                raise RuntimeError(
                    f"sphinx-apidoc failed: {proc_apidoc.stderr}\n"
                    f"Command: {' '.join(proc_apidoc.args)}"
                )
            
            # Generate modules documentation
            modules_rst = os.path.join(tmp_rst_dir, 'modules.rst')
            with open(modules_rst, 'w', encoding='utf-8') as f:
                f.write(f"{repo_name} Modules\n{'=' * (len(repo_name) + 8)}\n\n")
                
                for root, _, files in os.walk(src_dir):
                    for file in files:
                        if file.endswith('.py') and file != '__init__.py':
                            rel_path = Path(root, file).relative_to(src_dir)
                            module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')
                            f.write(f".. automodule:: {module_name}\n")
                            f.write("   :members:\n")
                            f.write("   :undoc-members:\n")
                            f.write("   :show-inheritance:\n\n")
            
            # Generate main index
            index_path = os.path.join(tmp_rst_dir, 'index.rst')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(f"""\
{repo_name} Documentation
{'=' * (len(repo_name) + 14)}

.. toctree::
   :maxdepth: 2
   :caption: Package Modules:

   modules

API Reference
=============

.. toctree::
   :maxdepth: 1
   
   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
""")
            
            # Build HTML documentation
            proc_build = subprocess.run([
                'sphinx-build',
                '-b', 'html',
                '-c', self.get_template_dir(),
                tmp_rst_dir,
                html_output_dir
            ], capture_output=True, text=True)
            
            if proc_build.returncode != 0:
                raise RuntimeError(
                    f"sphinx-build failed: {proc_build.stderr}\n"
                    f"Command: {' '.join(proc_build.args)}"
                )
            
            return html_output_dir

    def get_template_dir(self) -> str:
        """Get absolute path to Sphinx template directory"""
        return os.path.join(os.path.dirname(__file__), 'docs_template')