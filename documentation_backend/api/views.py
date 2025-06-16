import os
import shutil
import tempfile
import stat
import datetime
import re
import io

from git import Repo
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.files import File

from weasyprint import HTML
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import CodeDocumentation
from .serializers import CodeDocumentationSerializer, RegisterSerializer
from .doc_generators.factory import get_generator

# Глобальный CSS для всей документации
GLOBAL_PDF_CSS = """
<style>
    /* Общие стили */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 12pt;
        line-height: 1.6;
        color: #333;
        padding: 1.5cm;
        background: white;
    }
    
    /* Заголовки */
    h1, h2, h3, h4, h5, h6 {
        color: #1a365d;
        page-break-after: avoid;
    }
    h1 { font-size: 24pt; margin-top: 30px; margin-bottom: 20px; }
    h2 { font-size: 20pt; margin-top: 25px; margin-bottom: 15px; }
    h3 { font-size: 16pt; margin-top: 20px; margin-bottom: 10px; }
    
    /* Код и преформатированный текст */
    code, pre {
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: #f8f9fa;
        border: 1px solid #eaecef;
        border-radius: 4px;
        padding: 2px 4px;
    }
    pre {
        padding: 10px;
        overflow: auto;
        page-break-inside: avoid;
    }
    
    /* Таблицы */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        page-break-inside: avoid;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        font-weight: 600;
    }
    
    /* Ссылки */
    a {
        color: #2b6cb0;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    
    /* Списки */
    ul, ol {
        margin: 15px 0;
        padding-left: 30px;
    }
    li {
        margin-bottom: 8px;
    }
    
    /* Изображения и графики */
    img, svg, canvas, figure, .plotly-graph-div, .matplotlib-figure {
        max-width: 100% !important;
        max-height: 600px !important;
        height: auto !important;
        width: auto !important;
        display: block;
        margin: 20px auto;
        page-break-inside: avoid;
    }
    
    /* Блоки с кодом */
    .code-block {
        background: #f5f7f9;
        border-left: 4px solid #2b6cb0;
        padding: 10px 15px;
        margin: 15px 0;
        page-break-inside: avoid;
    }
    
    /* Разделители */
    hr {
        border: 0;
        height: 1px;
        background: #e2e8f0;
        margin: 30px 0;
    }
</style>
"""


def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# --- Сбор метаданных Git ---
def collect_git_metadata(repo_path, max_releases=5, max_commits=10):
    repo = Repo(repo_path)
    tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
    releases = [{
        'version': t.name,
        'date': t.commit.committed_datetime.strftime('%Y-%m-%d'),
        'message': getattr(t.tag, 'message', '').strip()
    } for t in tags[:max_releases]]
    commits = repo.iter_commits(repo.active_branch.name, max_count=max_commits)
    recent_commits = [{
        'hash': c.hexsha[:7],
        'author': c.author.name,
        'date': datetime.datetime.fromtimestamp(c.committed_date).strftime('%Y-%m-%d'),
        'message': c.message.splitlines()[0]
    } for c in commits]
    return {'releases': releases, 'recent_commits': recent_commits}

# --- Генерация Release Notes ---

def create_release_notes_page(html_dir, metadata):
    """
    Создаёт HTML-страницу release_notes.html с перечислением релизов и связанных баг-фиксов.
    Для каждого релиза выводится заголовок версии и даты, основной текст сообщения,
    а потом список баг-фиксов, начинающихся с "*!", каждый в своей строке.
    """
    sections = []
    for rel in metadata['releases']:
        version = rel['version']
        date = rel['date']
        raw_msg = rel['message'] or ''
        # разбиваем сообщение по маркеру *!
        parts = raw_msg.split('*!')
        main_text = parts[0].strip()
        bug_items = [part.strip() for part in parts[1:] if part.strip()]
        # формируем HTML для баг-фиксов
        bugs_html = ''
        if bug_items:
            bugs_lines = ''.join(f"<li>*!{li}</li>" for li in bug_items)
            bugs_html = f"<ul>\n{bugs_lines}\n</ul>"
        # собираем секцию релиза
        section = (
            f"<h2>{version} — {date}</h2>"
            f"<p>{main_text}</p>"
            f"{bugs_html}"
        )
        sections.append(section)
    # добавляем недавние коммиты
    commits_html = ''
    recent = metadata.get('recent_commits', [])
    if recent:
        commit_lines = ''.join(
            f"<li><code>{c['hash']}</code> — {c['date']} ({c['author']}): {c['message']}</li>" for c in recent
        )
        commits_html = f"<h2>Recent Commits</h2><ul>\n{commit_lines}\n</ul>"
    # финальный HTML
    content = f"""<!DOCTYPE html>
<html>
<head><meta charset=\"utf-8\"><title>Release Notes & Latest Changes</title></head>
<body>
<h1>Release Notes & Latest Changes</h1>
{''.join(sections)}
{commits_html}
</body>
</html>"""
    path = os.path.join(html_dir, 'release_notes.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return 'release_notes.html'

# --- Помощники для названий и списка страниц ---
def extract_title(html_dir, page):
    path = os.path.join(html_dir, page)
    try:
        text = open(path, 'r', encoding='utf-8').read()
        m = re.search(r'<title>(.*?)</title>', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.IGNORECASE|re.DOTALL)
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()[:100] if m else page.replace('.html','').replace('_',' ').title()
    except:
        return page

# --- Title Page ---
def create_title_page(html_dir, repo_name):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    safe = repo_name.replace('<','&lt;').replace('>','&gt;')
    content = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{safe}</title></head><body>
<h1>{safe}</h1><p>Техническая документация</p><p>Сгенерировано: {now}</p>
</body></html>"""
    p = os.path.join(html_dir, 'title_page.html')
    with open(p, 'w', encoding='utf-8') as f: f.write(content)
    return 'title_page.html'

# --- Table of Contents с номерами страниц ---
def create_toc_page(html_dir, entries):
    # entries: list of (page, title, start_page)
    items = []
    for _, title, start in entries:
        items.append(f"<li>{title} ........................................ {start}</li>")
    content = f"""<!DOCTYPE html>
<html><head><meta charset=\"utf-8\"><title>Содержание</title></head><body>
<h1>Содержание</h1>
<ul>
{''.join(items)}
</ul>
</body></html>"""
    path = os.path.join(html_dir, 'toc.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return 'toc.html'

# --- Получение основных HTML страниц ---
def get_main_html_files(html_dir):
    """
    Собирает до 20 основных HTML страниц (кроме титулки, оглавления и релизов) для включения в PDF.
    """
    pages = []
    for fname in sorted(os.listdir(html_dir)):
        if fname.endswith('.html') and fname not in ('title_page.html', 'toc.html', 'release_notes.html'):
            pages.append(fname)
    return pages[:20]

# --- Создание CSS файла ---
def create_css_file(html_dir):
    css_path = os.path.join(html_dir, 'pdf_styles.css')
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(GLOBAL_PDF_CSS)
    return css_path

# --- Генерация полного PDF с порядком и оглавлением ---
# Обновлено: удалена вторая дублирующаяся реализация функции

def generate_full_pdf_from_html(html_dir, pdf_path):
    css = create_css_file(html_dir)
    title_page = 'title_page.html'
    release_page = 'release_notes.html'
    content_pages = get_main_html_files(html_dir)
    counts = {}
    merger = PdfMerger()
    pages_to_count = [release_page] + content_pages
    for page in pages_to_count:
        p = os.path.join(html_dir, page)
        if os.path.exists(p):
            pdf_bytes = HTML(p).write_pdf(stylesheets=[css], presentational_hints=True)
            reader = PdfReader(io.BytesIO(pdf_bytes))
            counts[page] = len(reader.pages)
    current = 1
    start_release = current + 1
    current += counts.get(release_page, 0)
    starts = [
        (release_page, extract_title(html_dir, release_page), start_release),
    ]
    for page in content_pages:
        start = current + 1
        starts.append((page, extract_title(html_dir, page), start))
        current += counts.get(page, 0)
    toc_page = create_toc_page(html_dir, starts)
    merge_order = [title_page, toc_page, release_page] + content_pages
    for page in merge_order:
        p = os.path.join(html_dir, page)
        if os.path.exists(p):
            merger.append(io.BytesIO(HTML(p).write_pdf(stylesheets=[css], presentational_hints=True)))
    with open(pdf_path, 'wb') as f:
        merger.write(f)
    merger.close()

# --- Добавление номеров страниц (начиная с toc) ---
def add_page_numbers_to_pdf(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if i >= 1:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.drawCentredString(300, 15, f"{i}")
            can.save()
            packet.seek(0)
            wm = PdfReader(packet).pages[0]
            page.merge_page(wm)
        writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)

class GenerateDocsView(APIView):
    def post(self, request):
        repo_url = request.data.get('repo_url')
        if not repo_url:
            return Response({'error':'Не указан repo_url'}, status=400)
        name = repo_url.rstrip('/').split('/')[-1].replace('.git','')
        html_dir = os.path.join(settings.MEDIA_ROOT, 'docs', name, 'html')
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'docs', name, 'documentation.pdf')
        # очистка
        if os.path.exists(html_dir): shutil.rmtree(html_dir, onerror=remove_readonly)
        if os.path.exists(pdf_path): os.remove(pdf_path)
        tmp = tempfile.mkdtemp()
        try:
            Repo.clone_from(repo_url, tmp)
            git_md = collect_git_metadata(tmp)
            gen = get_generator(tmp)
            docs_path = gen.generate(tmp, name)
            if not os.path.isdir(docs_path):
                raise FileNotFoundError(f"docs_path не найден: {docs_path}")
            os.makedirs(html_dir, exist_ok=True)
            shutil.copytree(docs_path, html_dir, dirs_exist_ok=True)
            # title page
            create_title_page(html_dir, name)
            # release notes
            create_release_notes_page(html_dir, git_md)
            # generate PDF + toc
            generate_full_pdf_from_html(html_dir, pdf_path)
            add_page_numbers_to_pdf(pdf_path, pdf_path)
            # save
            doc = CodeDocumentation(
                user=request.user if request.user.is_authenticated else None,
                title=f"Documentation {name}",
                content=f"Автогенерация из {repo_url}",
                code_example=""
            )
            with open(pdf_path,'rb') as f:
                doc.pdf_file.save(f'{name}.pdf', File(f), save=True)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        finally:
            shutil.rmtree(tmp, onerror=remove_readonly)
        return Response({'pdf_url': doc.pdf_file.url}, status=201)
    
class DocumentListView(APIView):
    def get(self, request):
        docs = CodeDocumentation.objects.all().order_by('-created_at')
        serializer = CodeDocumentationSerializer(docs, many=True, context={'request': request})
        return Response(serializer.data)

class DocumentGenerateView(APIView):
    def post(self, request):
        repo_url = request.data.get('repo_url')
        if not repo_url:
            return Response({'error': 'Не указан URL репозитория'}, status=400)
        # Здесь можно использовать существующую логику генерации (например, вызвать GenerateDocsView.post)
        # Для простоты — создаём запись в базе и возвращаем её
        doc = CodeDocumentation.objects.create(
            title=f"Документация для {repo_url}",
            content="Документация сгенерирована.",
            code_example=""
        )
        serializer = CodeDocumentationSerializer(doc)
        return Response(serializer.data, status=201)

class DocumentDownloadPdfView(APIView):
    def get(self, request, pk):
        try:
            doc = CodeDocumentation.objects.get(pk=pk)
        except CodeDocumentation.DoesNotExist:
            raise Http404
        # Путь к PDF (пример)
        pdf_path = os.path.join('media', 'docs', f'doc_{pk}', 'documentation.pdf')
        if not os.path.exists(pdf_path):
            return Response({'error': 'PDF не найден'}, status=404)
        return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')

class DocumentDownloadHtmlView(APIView):
    def get(self, request, pk):
        try:
            doc = CodeDocumentation.objects.get(pk=pk)
        except CodeDocumentation.DoesNotExist:
            raise Http404
        # Путь к HTML (пример)
        html_path = os.path.join('media', 'docs', f'doc_{pk}', 'html', 'index.html')
        if not os.path.exists(html_path):
            return Response({'error': 'HTML не найден'}, status=404)
        return FileResponse(open(html_path, 'rb'), content_type='text/html')

class UploadFileView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'Файл не передан'}, status=400)
        # Сохраняем файл (пример)
        save_path = os.path.join('media', 'uploads', file.name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        return Response({'download_url': f'/media/uploads/{file.name}'})

class GenerateLocalDocsView(APIView):
    def post(self, request):
        repo_url = request.data.get('repo_url')
        if not repo_url:
            return Response({'error': 'Не указан путь к репозиторию'}, status=400)
        # Здесь должна быть логика генерации документации по локальному пути
        # Для примера — просто создаём запись
        doc = CodeDocumentation.objects.create(
            title=f"Локальная документация для {repo_url}",
            content="Документация сгенерирована по локальному репозиторию.",
            code_example=""
        )
        serializer = CodeDocumentationSerializer(doc)
        return Response(serializer.data, status=201)

class DocumentDeleteView(APIView):
    def delete(self, request, pk):
        try:
            doc = CodeDocumentation.objects.get(pk=pk)
        except CodeDocumentation.DoesNotExist:
            raise Http404
        doc.delete()
        return Response(status=204)

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)