import { Component } from '@angular/core';
import { RepoService } from '../../services/repo.service';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './upload.component.html'
})
export class UploadComponent {
  repoUrl = '';
  docs: any = null;
  loading = false;
  error = '';

  constructor(private repoService: RepoService) {}

  onUpload() {
    if (!this.repoUrl) return;
    this.loading = true;
    this.error = '';
    this.repoService.uploadRepoUrl(this.repoUrl).subscribe({
      next: (data) => {
        this.docs = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Ошибка загрузки';
        this.loading = false;
      }
    });
  }
}
