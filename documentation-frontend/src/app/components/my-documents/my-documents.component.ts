import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DocumentService } from '../../services/document.service';

@Component({
  selector: 'app-my-documents',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './my-documents.component.html',
  styleUrls: ['./my-documents.component.css']
})
export class MyDocumentsComponent implements OnInit {
  documents: any[] = [];
  loading = false;
  error: string | null = null;

  constructor(private documentService: DocumentService) {}

  ngOnInit() {
    this.loadDocuments();
  }

  loadDocuments() {
    this.loading = true;
    this.error = null;
    this.documentService.getDocuments().subscribe({
      next: (docs) => {
        this.documents = docs;
        this.loading = false;
      },
      error: (err) => {
        this.error = err.error?.error || 'Ошибка при загрузке документов';
        this.loading = false;
      }
    });
  }

  getStatusText(status: string): string {
    switch (status) {
      case 'completed': return 'Готово';
      case 'pending': return 'В очереди';
      case 'processing': return 'В процессе';
      case 'failed': return 'Ошибка';
      default: return status;
    }
  }

  viewHtml(doc: any) {
    if (doc.html_path) {
      window.open(`http://localhost:8000/${doc.html_path}`, '_blank', 'width=1024,height=768');
    }
  }

  deleteDocument(doc: any) {
    if (!confirm('Вы действительно хотите удалить этот документ?')) return;
    this.documentService.deleteDocument(doc.id).subscribe({
      next: () => {
        this.loadDocuments();
      },
      error: (err: any) => {
        this.error = err.error?.error || 'Ошибка при удалении документа';
      }
    });
  }
} 