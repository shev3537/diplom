# api/tasks.py
from celery import shared_task

@shared_task
def generate_docs_task(repo_url, repo_name):
    import os, shutil, tempfile, stat, time
    from git import Repo
    from django.conf import settings
    from .doc_generators.factory import get_generator
    from weasyprint import HTML
    from PyPDF2 import PdfMerger

    def remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def get_main_html_files(html_dir):
        main_pages = [
            'index.html', 'modules.html', 'classes.html', 'files.html', 'annotated.html'
        ]
        pages = [f for f in main_pages if os.path.exists(os.path.join(html_dir, f))]
        if not pages:
            pages = sorted([f for f in os.listdir(html_dir) if f.endswith('.html')])[:10]
        return pages

    def generate_full_pdf_from_html(html_dir, output_pdf_path, pages):
        pdf_files = []
        for page in pages:
            html_path = os.path.join(html_dir, page)
            pdf_path = html_path.replace('.html', '.pdf')
            HTML(html_path).write_pdf(pdf_path)
            pdf_files.append(pdf_path)
        merger = PdfMerger()
        for pdf in pdf_files:
            merger.append(pdf)
        merger.write(output_pdf_path)
        merger.close()
        for pdf in pdf_files:
            os.remove(pdf)

    html_output_dir = os.path.join(settings.MEDIA_ROOT, 'docs', repo_name, 'html')
    pdf_output_path = os.path.join(settings.MEDIA_ROOT, 'docs', repo_name, 'documentation.pdf')

    if os.path.exists(html_output_dir):
        shutil.rmtree(html_output_dir, onerror=remove_readonly)
    if os.path.exists(pdf_output_path):
        os.remove(pdf_output_path)

    tmp_dir = tempfile.mkdtemp()
    try:
        Repo.clone_from(repo_url, tmp_dir)
        generator = get_generator(tmp_dir)
        docs_path = generator.generate(tmp_dir, repo_name)
        dest_dir = html_output_dir
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir, onerror=remove_readonly)
        shutil.copytree(docs_path, dest_dir)
        pages = get_main_html_files(dest_dir)
        if pages:
            generate_full_pdf_from_html(dest_dir, pdf_output_path, pages)
    finally:
        time.sleep(1)
        shutil.rmtree(tmp_dir, onerror=remove_readonly)
