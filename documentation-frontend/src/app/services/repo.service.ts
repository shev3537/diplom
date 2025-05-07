import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class RepoService {
  private apiUrl = 'http://localhost:8000/api/';

  constructor(private http: HttpClient) {}

  uploadRepoUrl(url: string): Observable<any> {
    return this.http.post(this.apiUrl + 'upload-repo-url/', { repo_url: url });
  }
}
