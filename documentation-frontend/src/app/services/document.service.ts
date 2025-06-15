import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class DocumentService {
  private apiUrl = 'http://localhost:8000/api/documents';

  constructor(private http: HttpClient) {}

  // Генерация документации по новому реальному эндпоинту
  generateDocsReal(repoUrl: string): Observable<any> {
    return this.http.post<any>('http://localhost:8000/api/generate-docs/', { repo_url: repoUrl });
  }

  // Получение списка документов
  getDocuments(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }

  // Скачивание PDF
  downloadPdf(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${id}/download_pdf`, { responseType: 'blob' });
  }

  // Скачивание HTML
  downloadHtml(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${id}/download_html`, { responseType: 'blob' });
  }

  // Удаление документа
  deleteDocument(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}/`);
  }
}
