import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = 'http://127.0.0.1:8000/api/';

  constructor(private http: HttpClient) {}

  register(username: string, email: string, password: string): Observable<any> {
    return this.http.post(this.apiUrl + 'register/', { username, email, password });
  }

  login(username: string, password: string): Observable<any> {
    return this.http.post(this.apiUrl + 'login/', { username, password });
  }
}