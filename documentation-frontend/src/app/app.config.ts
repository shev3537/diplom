import { ApplicationConfig } from '@angular/core';
import { provideRouter, Routes } from '@angular/router';
import { UploadComponent } from './components/upload/upload.component';
import { provideHttpClient } from '@angular/common/http';
import { withFetch } from '@angular/common/http';

const routes: Routes = [
  { path: '', component: UploadComponent }
];

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withFetch()),
  ],
};
