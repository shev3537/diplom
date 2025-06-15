import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root' // Автоматическая регистрация сервиса
})
export class UploadService {
  private apiUrl = 'http://localhost:8000/api/upload'; // URL Django-сервера

  constructor(private http: HttpClient) {}

  // Загрузка файла на сервер
  uploadFile(file: File): Observable<{ download_url: string }> {
    const formData = new FormData();
    formData.append('file', file, file.name); // 'file' — ключ, должен совпадать с ожидаемым на бэкенде

    return this.http.post<{ download_url: string }>(this.apiUrl, formData).pipe(
      catchError((error: HttpErrorResponse) => {
        console.error('Upload error:', error.message);
        return throwError(() => new Error('File upload failed'));
      })
    );
  }
}