import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class DownloadService {
  download(format: string) {
    let url = '';
    if (format === 'pdf') {
      url = 'http://localhost:8000/api/download-document/';
    } else if (format === 'html') {
      url = 'http://localhost:8000/api/download-document-html/';
    } else if (format === 'docx') {
      url = 'http://localhost:8000/api/download-document-docx/';
    }
    window.open(url, '_blank');
  }
}
