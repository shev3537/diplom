import { Component, OnInit } from '@angular/core';
import { DocumentService } from '../../services/document.service';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './upload.component.html'
})
export class UploadComponent implements OnInit {
  genRepoUrl = '';
  genLoading = false;
  genError = '';
  genSuccess = false;
  genResult: any = null;
  documents: any[] = [];

  constructor(private documentService: DocumentService) {}

  ngOnInit() {
    this.loadDocuments();
  }

  // Генерация документации через реальный эндпоинт
  generateDoc() {
    if (!this.genRepoUrl) return;
    this.genLoading = true;
    this.genError = '';
    this.genSuccess = false;
    this.genResult = null;
    this.documentService.generateDocsReal(this.genRepoUrl).subscribe({
      next: (res: any) => {
        this.genSuccess = true;
        this.genLoading = false;
        this.genResult = res; // Здесь будут doc_url и pdf_url
      },
      error: (err: any) => {
        this.genError = err.error?.error || 'Ошибка при генерации';
        this.genLoading = false;
      }
    });
  }

  loadDocuments() {
    this.documentService.getDocuments().subscribe(
      docs => this.documents = docs,
      error => console.error('Ошибка при загрузке документов:', error)
    );
  }

  getStatusText(status: string): string {
    const statusMap: { [key: string]: string } = {
      'pending': 'В обработке',
      'completed': 'Завершено',
      'failed': 'Ошибка'
    };
    return statusMap[status] || status;
  }

  downloadPdf(doc: any) {
    this.documentService.downloadPdf(doc.id).subscribe(blob => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${doc.title}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    });
  }

  downloadHtml(doc: any) {
    this.documentService.downloadHtml(doc.id).subscribe(blob => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${doc.title}.html`;
      link.click();
      window.URL.revokeObjectURL(url);
    });
  }
}
