import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { catchError, of } from 'rxjs';

interface Documentation {
  title: string;
  description: string;
  code: string;
}

@Component({
  selector: 'app-code-docs',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  template: `
    <h2>Документация по коду</h2>
    
    @if (isLoading) {
      <div class="loading">Загрузка...</div>
    }
    @else if (errorMessage) {
      <div class="error">{{ errorMessage }}</div>
    }
    @else {
      @for (item of docs; track item.title) {
        <div class="doc-item">
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
          <pre>{{ item.code }}</pre>
        </div>
      } @empty {
        <p>Документация отсутствует</p>
      }
    }
  `,
  styles: [`
    .doc-item {
      margin-bottom: 2rem;
      padding: 1rem;
      border: 1px solid #eee;
      border-radius: 4px;
      background: white;
    }
    pre {
      background: #f5f5f5;
      padding: 1rem;
      overflow-x: auto;
      border-radius: 4px;
      font-family: monospace;
    }
    .loading {
      color: #666;
      font-style: italic;
    }
    .error {
      color: #d32f2f;
      padding: 1rem;
      background: #ffebee;
      border-radius: 4px;
    }
  `]
})
export class CodeDocsComponent implements OnInit {
  docs: Documentation[] = [];
  isLoading = true;
  errorMessage: string | null = null;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadDocumentation();
  }

  loadDocumentation() {
    this.isLoading = true;
    this.errorMessage = null;

    this.apiService.getDocumentation().pipe(
      catchError((error: any) => {
        console.error('API Error:', error);
        this.errorMessage = this.getErrorMessage(error);
        return of([]); // Возвращаем пустой массив при ошибке
      })
    ).subscribe({
      next: (data: Documentation[]) => {
        this.docs = data;
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = this.getErrorMessage(err);
      }
    });
  }

  private getErrorMessage(error: any): string {
    if (error.status === 0) {
      return 'Не удалось подключиться к серверу. Проверьте:'
        + '\n1. Запущен ли бэкенд (Django)'
        + '\n2. Правильный ли URL в api.service.ts';
    }
    return `Ошибка сервера: ${error.message || 'Неизвестная ошибка'}`;
  }
}