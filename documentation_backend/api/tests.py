from django.test import TestCase
from .models import CodeDocumentation, APIDocumentation, DatabaseSchema
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
import tempfile
from git import Repo
import os
import ast
from django.test import TestCase
from .views import extract_docstrings, parse_readme

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_code_doc_creation(self):
        doc = CodeDocumentation.objects.create(
            title='Python Basics',
            content='Introduction to Python',
            code_example='print("Hello World")'
        )
        self.assertEqual(doc.title, 'Python Basics')
        self.assertTrue(doc.created_at)

    def test_api_doc_creation(self):
        api_doc = APIDocumentation.objects.create(
            endpoint='/api/users/',
            method='GET',
            description='Get user list',
            parameters={'query': 'username'},
            responses={'200': 'Success'}
        )
        self.assertEqual(api_doc.method, 'GET')
        self.assertIsInstance(api_doc.parameters, dict)

    def test_db_schema_creation(self):
        schema = DatabaseSchema.objects.create(
            name='User Schema',
            schema={'fields': ['id', 'username']},
            description='User database structure'
        )
        self.assertIn('username', schema.schema['fields'])
class UploadRepoViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('upload-repo-url')
        
        # Создаем временный тестовый репозиторий
        self.temp_dir = tempfile.mkdtemp()
        self.repo = Repo.init(self.temp_dir)
        readme_path = os.path.join(self.temp_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write("# Test Repo\n\nExample repo for testing")

    def test_valid_repo_url(self):
        # Тестируем с локальным путём вместо реального URL
        response = self.client.post(
            self.url,
            {'repo_url': self.temp_dir},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('readme', response.data)
        self.assertIn('commits', response.data)

    def test_invalid_repo_url(self):
        response = self.client.post(
            self.url,
            {'repo_url': 'invalid_url'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_missing_repo_url(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'No repo_url provided')

    def tearDown(self):
        # Очистка временных файлов
        if os.path.exists(self.temp_dir):
            self.repo.close()
            shutil.rmtree(self.temp_dir, onerror=lambda func, path, _: os.chmod(path, stat.S_IWRITE))
class UtilityTests(TestCase):
    def setUp(self):
        self.test_file = """
        \'''Module docstring\'''
        class MyClass:
            \'''Class docstring\'''
            def my_method(self):
                \'''Method docstring\'''
                pass
            
        @route('/api')
        def my_view():
            \'''View docstring\'''
            pass
        """
        
    def test_extract_docstrings(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write(self.test_file)
            f.close()
            result = extract_docstrings(f.name)
            os.unlink(f.name)
            
        self.assertEqual(result['module_docstring'], 'Module docstring')
        self.assertEqual(len(result['classes']), 1)
        self.assertEqual(result['functions'][0]['name'], 'my_view')
        self.assertEqual(len(result['api_endpoints']), 1)

    def test_readme_parsing(self):
        temp_dir = tempfile.mkdtemp()
        readme_path = os.path.join(temp_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write("# Test Title\n\n* List item")
        
        result = parse_readme(temp_dir)
        self.assertIn('Test Title', result['content'])
        self.assertIn('<h1>', result['content'])
        shutil.rmtree(temp_dir)
