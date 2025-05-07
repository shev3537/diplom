import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-github-doc',
  templateUrl: './github-doc.component.html',
  styleUrls: ['./github-doc.component.css']
})
export class GithubDocComponent {
  githubUrl: string = '';
  isLoading: boolean = false;
  error: string = '';
  pdfPreviewUrl: string | null = null;

  constructor(private http: HttpClient) {}

  generateDocumentation() {
    if (!this.githubUrl) {
      this.error = 'Please enter a valid GitHub URL';
      return;
    }

    this.isLoading = true;
    this.error = '';
    this.pdfPreviewUrl = null;

    this.http.post(
      'http://localhost:8000/api/generate-from-github/',
      { url: this.githubUrl },
      { responseType: 'blob' }
    ).subscribe({
      next: (pdfBlob: Blob) => {
        this.pdfPreviewUrl = URL.createObjectURL(pdfBlob);
        this.isLoading = false;
      },
      error: (err) => {
        this.error = 'Failed to generate documentation. Check the URL or try later.';
        this.isLoading = false;
        console.error(err);
      }
    });
  }

  downloadPdf() {
    if (this.pdfPreviewUrl) {
      const link = document.createElement('a');
      link.href = this.pdfPreviewUrl;
      link.download = `documentation_${new Date().toISOString().slice(0, 10)}.pdf`;
      link.click();
    }
  }
}