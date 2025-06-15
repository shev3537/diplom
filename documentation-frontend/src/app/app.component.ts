import { Component } from '@angular/core';
import { DocumentService } from './services/document.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './components/header/header.component';

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  imports: [
    CommonModule,
    FormsModule,
    RouterOutlet,
    HeaderComponent
  ]
})
export class AppComponent {
  title = 'documentation-frontend';
  repoUrl: string = '';
  docUrl: string | null = null;
  pdfUrl: string | null = null;
  loading: boolean = false;
  error: string | null = null;

  private backendBaseUrl = 'http://localhost:8000';

  constructor(private documentService: DocumentService) {}

  generateDocs() {
    console.log('generateDocs вызван' , this.repoUrl);
    this.error = null;
    this.loading = true;
    this.docUrl = null;
    this.pdfUrl = null;
    this.documentService.generateDocsReal(this.repoUrl).subscribe({
      next: (res: any) => {
        this.docUrl = this.backendBaseUrl + res.doc_url;
        this.pdfUrl = this.backendBaseUrl + res.pdf_url;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = err.error?.error || 'Ошибка при генерации документации';
        this.loading = false;
      }
    });
  }

  isLoggedIn() {
    try {
      return typeof window !== 'undefined' && !!window.localStorage.getItem('token');
    } catch {
      return false;
    }
  }
}
