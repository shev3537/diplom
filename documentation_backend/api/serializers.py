from rest_framework import serializers
from .models import CodeDocumentation, APIDocumentation, DatabaseSchema, CustomUser
import os

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class CodeDocumentationSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()
    html_path = serializers.SerializerMethodField()

    class Meta:
        model = CodeDocumentation
        fields = '__all__'
        read_only_fields = ('pdf_file',)

    def get_pdf_url(self, obj):
        if obj.pdf_file and hasattr(obj.pdf_file, 'url'):
            return f"http://localhost:8000{obj.pdf_file.url}"
        return None

    def get_html_path(self, obj):
        if obj.pdf_file and hasattr(obj.pdf_file, 'name'):
            pdf_name = os.path.basename(obj.pdf_file.name)
            doc_base = pdf_name.split('_documentation')[0]
            html_path = os.path.join('media', 'docs', doc_base, 'html', 'index.html')
            abs_html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), html_path)
            if os.path.exists(abs_html_path):
                return html_path
        return None

class APIDocumentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIDocumentation
        fields = '__all__'

class DatabaseSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseSchema
        fields = '__all__'