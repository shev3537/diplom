import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  username = '';
  email = '';
  password = '';
  error = '';
  success = false;

  constructor(private http: HttpClient) {}

  register() {
    this.error = '';
    this.success = false;
    this.http.post('http://localhost:8000/api/register/', {
      username: this.username,
      email: this.email,
      password: this.password
    }).subscribe({
      next: () => this.success = true,
      error: (err: any) => {
        this.error = err.error?.username?.[0] || err.error?.email?.[0] || err.error?.password?.[0] || 'Ошибка регистрации';
      }
    });
  }
} 