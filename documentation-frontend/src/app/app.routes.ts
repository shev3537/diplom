import { Routes } from '@angular/router';
import { UploadComponent } from './components/upload/upload.component';
import { AuthComponent } from './auth/auth.component';
import { AuthGuard } from './services/auth-guard.service';
import { HomeComponent } from './components/home/home.component';
import { MyDocumentsComponent } from './components/my-documents/my-documents.component';
import { RegisterComponent } from './components/register/register.component';

export const routes: Routes = [
  { path: '', component: AuthComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'home', component: HomeComponent, canActivate: [AuthGuard] },
  { path: 'upload', component: UploadComponent, canActivate: [AuthGuard] },
  { path: 'my-docs', component: MyDocumentsComponent, canActivate: [AuthGuard] },
  { path: '**', redirectTo: '' }
];