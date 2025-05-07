import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { catchError, of } from 'rxjs';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { HeaderComponent } from './components/header/header.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    RouterOutlet,
    HeaderComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  selectedFile: File | null = null; // Выбранный файл
  downloadUrl: string | null = null; // URL для скачивания файла

  constructor(private http: HttpClient) {}

  // Обработчик выбора файла
  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0];
    console.log('Файл выбран:', this.selectedFile);
  }

  // Обработчик загрузки файла
  onUpload(): void {
    if (this.selectedFile) {
      const formData = new FormData();
      formData.append('file', this.selectedFile, this.selectedFile.name);

      this.http.post<any>('http://localhost:8000/api/upload/', formData)
        .pipe(
          catchError(error => {
            console.error('Ошибка загрузки файла:', error);
            return of(null);
          })
        )
        .subscribe(response => {
          if (response) {
            console.log('Ответ сервера:', response);
            this.downloadUrl = response.pdf_documentation; // URL для скачивания
          }
        });
    } else {
      alert('Пожалуйста, выберите файл.');
    }
  }

  // Обработчик скачивания файла
  downloadFile(): void {
    if (this.downloadUrl) {
      window.open(this.downloadUrl, '_blank');
    }
  }
}
