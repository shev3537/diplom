import { Routes } from '@angular/router';
import { UploadComponent } from './components/upload/upload.component';


export const routes: Routes = [
  {
    path: 'code-docs',
    loadComponent: () => import('./components/code-docs/code-docs.component').then(m => m.CodeDocsComponent),
    title: 'Документация по коду'
  },
  { path: 'upload', component: UploadComponent },
  {
    path: 'api-docs',
    loadComponent: () => import('./components/api-docs/api-docs.component').then(m => m.ApiDocsComponent),
    title: 'API Документация'
  },
  {
    path: 'db-docs',
    loadComponent: () => import('./components/db-docs/db-docs.component').then(m => m.DbDocsComponent),
    title: 'Документация БД'
  },
  { path: '', redirectTo: 'code-docs', pathMatch: 'full' },
  { path: '**', redirectTo: 'code-docs' }
];