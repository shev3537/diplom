import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

interface Documentation {
  title: string;
  description: string;
  code: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://127.0.0.1:8000/api/';

  constructor(private http: HttpClient) {}

  // Загрузка кода для генерации документации
  uploadCode(file: File): Observable<HttpEvent<any>> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.baseUrl}upload/`, formData, {
      reportProgress: true,
      observe: 'events'
    });
  }

  // Получение сгенерированной документации
  getDocumentation(): Observable<Documentation[]> {
    return this.http.get<Documentation[]>(`${this.baseUrl}documentation/`);
  }

  // Скачивание документации в виде файла
  downloadDocumentation(): Observable<Blob> {
    return this.http.get(`${this.baseUrl}download/`, { 
      responseType: 'blob' 
    });
  }

  // Дополнительный метод для получения конкретного раздела документации
  getDocumentationSection(sectionId: string): Observable<Documentation> {
    return this.http.get<Documentation>(`${this.baseUrl}documentation/${sectionId}/`);
  }
}