import { Component } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { FormsModule } from '@angular/forms';
import { NgIf } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [FormsModule, NgIf],
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.css']
})
export class AuthComponent {
  username = '';
  email = '';
  password = '';
  isLogin = true;
  message = '';

  constructor(private auth: AuthService, private router: Router) {}

  ngOnInit() {
    if (localStorage.getItem('token')) {
      this.router.navigate(['/code-docs']);
    }
  }

  submit() {
    if (this.isLogin) {
      this.auth.login(this.username, this.password).subscribe({
        next: res => {
          localStorage.setItem('token', res.token);
          this.message = 'Вход успешен!';
          this.router.navigate(['/code-docs']);
        },
        error: err => this.message = 'Ошибка входа'
      });
    } else {
      this.auth.register(this.username, this.email, this.password).subscribe({
        next: res => {
          localStorage.setItem('token', res.token);
          this.message = 'Регистрация успешна!';
          this.router.navigate(['/code-docs']);
        },
        error: err => this.message = 'Ошибка регистрации'
      });
    }
  }
}