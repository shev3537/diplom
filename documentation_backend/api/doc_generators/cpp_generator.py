import os
import subprocess
import tempfile
import datetime
import shutil
import logging
from pathlib import Path
from .base import DocGenerator

class CppDocGenerator(DocGenerator):
    def generate(self, repo_path: str, repo_name: str) -> str:
        # Проверяем доступность doxygen в системе
        if not shutil.which('doxygen'):
            raise EnvironmentError("Doxygen not found in PATH. Please install Doxygen.")

        # Создаем безопасную временную директорию для вывода
        output_dir = tempfile.mkdtemp(prefix='doxygen_')
        logging.info(f"Created temporary output directory: {output_dir}")
        
        try:
            config_path = self.create_doxygen_config(repo_path, output_dir)
            logging.info(f"Generated Doxygen config at: {config_path}")
            
            # Запускаем Doxygen с подробным выводом
            proc = subprocess.run(
                ['doxygen', config_path],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            # Сохраняем полные логи независимо от результата
            log_dir = os.path.join(output_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            with open(os.path.join(log_dir, 'doxygen_stdout.log'), 'w') as f:
                f.write(proc.stdout)
            with open(os.path.join(log_dir, 'doxygen_stderr.log'), 'w') as f:
                f.write(proc.stderr)
            
            # Проверяем результат выполнения
            if proc.returncode != 0:
                logging.error(f"Doxygen failed with exit code {proc.returncode}")
                logging.error(f"Stderr: {proc.stderr[:500]}...")
                raise RuntimeError(
                    f"Doxygen generation failed. See logs in {log_dir} for details."
                )
            
            # Возвращаем путь к сгенерированной документации
            html_output = os.path.join(output_dir, 'html')
            if not os.path.exists(html_output):
                raise FileNotFoundError(f"HTML output not found at {html_output}")
            
            logging.info(f"Documentation successfully generated at: {html_output}")
            return html_output
            
        except Exception as e:
            # Сохраняем временную директорию для диагностики
            logging.error(f"Documentation generation failed: {str(e)}")
            logging.info(f"Temporary files preserved at: {output_dir}")
            raise

    def create_doxygen_config(self, repo_path: str, output_dir: str) -> str:
        """Создает конфигурационный файл для Doxygen без исключений"""
        config_path = os.path.join(repo_path, 'Doxyfile')
        
        # Формируем конфиг с полным включением всех файлов
        config_content = f"""
# Основные настройки
PROJECT_NAME           = "C/C++ project"
PROJECT_NUMBER         = "Generated on {datetime.datetime.now().strftime('%Y-%m-%d')}"
OUTPUT_DIRECTORY       = {output_dir}
RECURSIVE              = YES
EXTRACT_ALL            = YES
EXTRACT_PRIVATE        = YES
EXTRACT_STATIC         = YES
INPUT                  = .
GENERATE_HTML          = YES
HAVE_DOT               = YES
CALL_GRAPH             = YES
CALLER_GRAPH           = YES
GENERATE_LATEX         = NO
QUIET                  = NO
WARNINGS               = YES
"""

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
            
        return config_path