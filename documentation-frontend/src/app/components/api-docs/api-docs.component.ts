import { Component } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-api-docs',
  standalone: true,
  imports: [CommonModule],
  template: `<h2>API Документация</h2>`,
  // ... аналогично code-docs
})
export class ApiDocsComponent {
  endpoints = [
    {
      method: 'GET',
      path: '/api/devices',
      description: 'Получить список устройств',
      params: [
        { name: 'status', type: 'boolean', required: false }
      ]
    }
  ];

  getMethodColor(method: string): string {
    const colors: Record<string, string> = {
      GET: 'bg-blue-100 text-blue-800',
      POST: 'bg-green-100 text-green-800',
      // ... другие методы
    };
    return colors[method] || 'bg-gray-100';
  }
}
