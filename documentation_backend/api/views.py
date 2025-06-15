import os
import shutil
import tempfile
import stat
import time
import datetime
import re
import io
from git import Repo
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from weasyprint import HTML
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import FileResponse, Http404
from .models import CodeDocumentation
from .serializers import CodeDocumentationSerializer, RegisterSerializer
from django.core.files import File
from rest_framework import status

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

def get_main_html_files(html_dir):
    if not os.path.exists(html_dir):
        print(f"Директория {html_dir} не существует")
        return []
        
    standard_pages = ['index.html', 'main.html', 'home.html', 'contents.html']
    found_pages = [p for p in standard_pages if os.path.exists(os.path.join(html_dir, p))]
    mandatory_pages = ['nfapi_call_flow.html', 'md_CHANGELOG.html']
    for page in mandatory_pages:
        page_path = os.path.join(html_dir, page)
        if os.path.exists(page_path) and page not in found_pages:
            found_pages.append(page)
        else:
            print(f"Файл {page} не найден в {html_dir}")
    
    if found_pages:
        return found_pages
    
    content_pages = find_content_pages(html_dir)
    if content_pages:
        for page in mandatory_pages:
            if page not in content_pages and os.path.exists(os.path.join(html_dir, page)):
                content_pages.append(page)
        return content_pages
    
    all_html = sorted([f for f in os.listdir(html_dir) if f.endswith('.html')])
    for page in mandatory_pages:
        if page not in all_html and os.path.exists(os.path.join(html_dir, page)):
            all_html.append(page)
    return all_html[:20]

def find_content_pages(html_dir):
    content_pages = []
    exclude_terms = ['search', 'index', 'help', 'about', 'contact', 'genindex', 'py-modindex']
    main_files = [f for f in os.listdir(html_dir) if f.endswith('.html') and not any(term in f.lower() for term in exclude_terms)]
    for file in main_files:
        file_path = os.path.join(html_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if re.search(r'<h[1-3][^>]*>', content):
                    content_pages.append(file)
                elif len(content) > 3000:
                    content_pages.append(file)
        except Exception as e:
            print(f"Ошибка чтения {file_path}: {str(e)}")
            continue
    if content_pages:
        content_pages.sort(key=lambda f: os.path.getsize(os.path.join(html_dir, f)), reverse=True)
        return content_pages[:20]
    all_files = [f for f in os.listdir(html_dir) if f.endswith('.html') and not any(term in f.lower() for term in exclude_terms)]
    return all_files[:20] if all_files else None

def extract_html_links_from_changelog(html_dir):
    changelog_path = os.path.join(html_dir, 'md_CHANGELOG.html')
    if not os.path.exists(changelog_path):
        print(f"Файл md_CHANGELOG.html не найден в {html_dir}")
        return []
    try:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
        links = re.findall(r'href="([^"]+\.html)"', content)
        result = []
        for link in links:
            abs_path = os.path.normpath(os.path.join(html_dir, link))
            if os.path.exists(abs_path):
                fname = os.path.basename(abs_path)
                if fname not in result:
                    result.append(fname)
        return result
    except Exception as e:
        print(f"Ошибка извлечения ссылок из md_CHANGELOG.html: {e}")
        return []

def create_css_file(html_dir):
    """Создает внешний CSS файл для PDF документации"""
    css_path = os.path.join(html_dir, 'pdf_styles.css')
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(GLOBAL_PDF_CSS)
    return css_path

def create_title_page(html_dir, repo_name):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    safe_repo_name = repo_name.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    description = f"""
    Данная документация содержит полное техническое описание проекта {safe_repo_name}, 
    включая руководства пользователя, API reference, архитектурные решения и историю изменений.
    Документация сгенерирована автоматически на основе исходного кода проекта.
    """
    content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Project Documentation</title>
    <style>
        body.title-page {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: #ffffff;
            padding: 0;
            box-sizing: border-box;
        }}
        .container {{
            max-width: 800px;
            padding: 40px;
            border-radius: 8px;
            background: #fff;
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
        }}
        .header {{
            margin-bottom: 40px;
        }}
        .title-page h1 {{
            font-size: 36pt;
            color: #1a365d;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        .subtitle {{
            font-size: 20pt;
            color: #2b6cb0;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        .annotation {{
            font-size: 14pt;
            color: #4a5568;
            line-height: 1.6;
            text-align: center;
            padding: 30px;
            margin: 30px 0;
            border-top: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .info {{
            position: absolute;
            bottom: 30px;
            width: 100%;
            font-size: 10pt;
            color: #718096;
        }}
    </style>
</head>
<body class="title-page">
    <div class="container">
        <div class="header">
            <h1>{safe_repo_name}</h1>
            <div class="subtitle">Техническая документация</div>
        </div>
        <div class="annotation">
            {description}
        </div>
    </div>
    <div class="info">
        Сгенерировано: {now}
    </div>
</body>
</html>
"""
    path = os.path.join(html_dir, "title_page.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "title_page.html"

def create_toc_page(html_dir, pages):
    page_data = []
    changelog_links = extract_html_links_from_changelog(html_dir)
    
    # Добавляем основные страницы
    for page in pages:
        file_path = os.path.join(html_dir, page)
        fallback_title = os.path.basename(page).replace('.html', '').replace('_', ' ').title()
        title = fallback_title
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
            else:
                h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
                if h1_match:
                    title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                    if len(title) > 100:
                        title = title[:100] + '...'
        except Exception as e:
            print(f"Ошибка извлечения заголовка для {page}: {str(e)}")
        page_data.append((page, title))
    
    # Добавляем страницы из changelog
    for page in changelog_links:
        if page not in [p[0] for p in page_data]:  # Проверяем, что страница еще не добавлена
            file_path = os.path.join(html_dir, page)
            fallback_title = os.path.basename(page).replace('.html', '').replace('_', ' ').title()
            title = fallback_title
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()
                else:
                    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
                    if h1_match:
                        title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                        if len(title) > 100:
                            title = title[:100] + '...'
            except Exception as e:
                print(f"Ошибка извлечения заголовка для {page}: {str(e)}")
            page_data.append((page, title))

    # Сортируем страницы в правильном порядке
    main_pages = []
    changelog_pages = []
    
    # Сначала добавляем основные страницы в правильном порядке
    for page in pages:
        for p_data in page_data:
            if p_data[0] == page:
                main_pages.append(p_data)
                break
    
    # Затем добавляем страницы из changelog
    for p_data in page_data:
        if p_data[0] not in pages:
            changelog_pages.append(p_data)
    
    page_data = main_pages + changelog_pages
    
    toc_items = "\n".join(f'<li><a href="{page}" class="toc-link">{title}</a></li>' for page, title in page_data)
    content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Содержание</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 2cm;
            background: #ffffff;
        }}
        h1 {{
            color: #1a365d;
            font-size: 28pt;
            text-align: center;
            margin-bottom: 40px;
        }}
        .toc {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .toc-list {{
            list-style-type: none;
            padding: 0;
        }}
        .toc-list li {{
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .toc-link {{
            color: #2b6cb0;
            text-decoration: none;
            font-size: 14pt;
            font-weight: 500;
        }}
        .toc-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>Содержание</h1>
    <div class="toc">
        <ul class="toc-list">
            {toc_items}
        </ul>
    </div>
</body>
</html>
"""
    path = os.path.join(html_dir, "toc.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "toc.html"

def modify_html_for_pdf(html_dir, page, page_number):
    """Модифицирует HTML файл для добавления нумерации и якорей"""
    file_path = os.path.join(html_dir, page)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Добавляем якорь в начало body
        content = content.replace('<body', f'<body id="page_{page_number}"')
        
        # Добавляем стили для нумерации
        page_number_style = """
        @page {
            @bottom-center {
                content: counter(page);
                font-family: 'Helvetica', sans-serif;
                font-size: 9pt;
                color: #666666;
            }
        }
        """
        
        # Добавляем стили в head
        if '</head>' in content:
            content = content.replace('</head>', f'<style>{page_number_style}</style></head>')
        
        # Сохраняем модифицированный файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        print(f"Ошибка модификации HTML файла {page}: {str(e)}")

def generate_full_pdf_from_html(html_dir, pdf_output_path, all_pages):
    # Создаем внешний CSS файл
    css_path = create_css_file(html_dir)
    
    merger = PdfMerger()
    
    # Создаем титульный лист
    create_title_page(html_dir, "Документация 5G терминала")
    
    # Получаем ссылки из changelog
    changelog_links = extract_html_links_from_changelog(html_dir)
    
    # Создаем оглавление
    create_toc_page(html_dir, changelog_links)
    
    # Добавляем титульный лист
    title_page_path = os.path.join(html_dir, "title_page.html")
    if os.path.exists(title_page_path):
        pdf_bytes = HTML(title_page_path).write_pdf(
            stylesheets=[css_path],
            presentational_hints=True
        )
        pdf_file = io.BytesIO(pdf_bytes)
        merger.append(pdf_file)
    
    # Добавляем оглавление
    toc_path = os.path.join(html_dir, "toc.html")
    if os.path.exists(toc_path):
        pdf_bytes = HTML(toc_path).write_pdf(
            stylesheets=[css_path],
            presentational_hints=True
        )
        pdf_file = io.BytesIO(pdf_bytes)
        merger.append(pdf_file)
    
    # Обрабатываем основной файл changelog
    changelog_page = 'md_CHANGELOG.html'
    html_path = os.path.join(html_dir, changelog_page)
    
    if os.path.exists(html_path):
        # Генерируем PDF из основного файла
        pdf_bytes = HTML(html_path).write_pdf(
            stylesheets=[css_path],
            presentational_hints=True
        )
        pdf_file = io.BytesIO(pdf_bytes)
        merger.append(pdf_file)
    
    # Добавляем страницы из changelog_links
    for link in changelog_links:
        link_path = os.path.join(html_dir, link)
        if os.path.exists(link_path):
            pdf_bytes = HTML(link_path).write_pdf(
                stylesheets=[css_path],
                presentational_hints=True
            )
            pdf_file = io.BytesIO(pdf_bytes)
            merger.append(pdf_file)
    
    with open(pdf_output_path, "wb") as f_out:
        merger.write(f_out)
    merger.close()

def add_page_numbers_to_pdf(input_pdf_path, output_pdf_path):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)
    
    # Пропускаем титульную страницу и оглавление
    start_numbering_from = 2
    
    for i in range(total_pages):
        page = reader.pages[i]
        if i >= start_numbering_from:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            page_num = i - start_numbering_from + 1
            
            # Добавляем номер страницы внизу
            can.setFont("Helvetica", 9)
            can.setFillColorRGB(0.4, 0.4, 0.4)
            can.drawCentredString(300, 15, f"Страница {page_num}")
            
            # Добавляем якорь для навигации
            can.setFont("Helvetica", 1)
            can.drawString(10, 10, f"page_{page_num}")
            
            can.save()
            packet.seek(0)
            watermark = PdfReader(packet).pages[0]
            page.merge_page(watermark)
        
        writer.add_page(page)
    
    with open(output_pdf_path, "wb") as f_out:
        writer.write(f_out)

class GenerateDocsView(APIView):
    def post(self, request):
        print("=== НАЧАЛО ОБРАБОТКИ ЗАПРОСА ===")
        repo_url = request.data.get('repo_url')
        if not repo_url:
            return Response({'error': 'Не указан URL репозитория'}, status=400)

        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        html_output_dir = os.path.join(settings.MEDIA_ROOT, 'docs', repo_name, 'html')
        pdf_output_path = os.path.join(settings.MEDIA_ROOT, 'docs', repo_name, 'documentation.pdf')
        temp_pdf_path = os.path.join(settings.MEDIA_ROOT, 'docs', repo_name, 'temp_documentation.pdf')

        # Очистка предыдущей документации
        if os.path.exists(html_output_dir):
            shutil.rmtree(html_output_dir, onerror=remove_readonly)
        if os.path.exists(pdf_output_path):
            os.remove(pdf_output_path)
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

        tmp_dir = tempfile.mkdtemp()
        try:
            # Клонирование репозитория
            print(f"Клонирование репозитория: {repo_url}")
            Repo.clone_from(repo_url, tmp_dir)

            # Генерация HTML
            print("Генерация HTML документации...")
            generator = get_generator(tmp_dir)
            docs_path = generator.generate(tmp_dir, repo_name)

            # Проверяем, что docs_path существует
            if not os.path.exists(docs_path):
                raise FileNotFoundError(f"Путь к сгенерированной документации не существует: {docs_path}")

            # Копирование результатов
            print("Копирование сгенерированной документации...")
            os.makedirs(os.path.dirname(html_output_dir), exist_ok=True)
            shutil.copytree(docs_path, html_output_dir)

            # Проверяем наличие основного файла
            changelog_page = 'md_CHANGELOG.html'
            if not os.path.exists(os.path.join(html_output_dir, changelog_page)):
                raise FileNotFoundError(f"Основной файл документации {changelog_page} не найден")

            # Генерация PDF
            print("Сборка PDF документации...")
            generate_full_pdf_from_html(html_output_dir, pdf_output_path, [changelog_page])
            print("PDF успешно сгенерирован")

            # Сохраняем PDF в базу
            user = request.user if request.user.is_authenticated else None
            doc = CodeDocumentation(
                user=user,
                title=f"Документация для {repo_url}",
                content=f"Документация для {repo_url}",
                code_example=""
            )
            with open(pdf_output_path, 'rb') as pdf_f:
                doc.pdf_file.save(f'{repo_name}_documentation.pdf', File(pdf_f), save=True)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': f"Ошибка генерации документации: {str(e)}"}, status=500)
        finally:
            time.sleep(1)
            try:
                shutil.rmtree(tmp_dir, onerror=remove_readonly)
            except Exception as e:
                print(f"Ошибка удаления временной директории: {str(e)}")

        doc_url = f"{settings.MEDIA_URL}docs/{repo_name}/html/index.html"
        pdf_url = doc.pdf_file.url if doc.pdf_file else None
        return Response({
            'doc_url': doc_url,
            'pdf_url': pdf_url,
            'message': 'Документация успешно сгенерирована'
        })

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