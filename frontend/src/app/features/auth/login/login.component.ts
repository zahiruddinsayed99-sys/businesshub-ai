import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private router = inject(Router);

  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });
  loading = false;
  error = '';

  onSubmit() {
    if (this.loginForm.invalid) {
      return;
    }

    this.loading = true;
    this.error = '';

    const val = this.loginForm.value;

    this.http.post<{ access_token: string, organization_id?: string }>(`${environment.apiUrl}/auth/login`, {
      email: val.email,
      password: val.password
    }).subscribe({
      next: (res) => {
        try {
          if (typeof localStorage !== 'undefined') {
            localStorage.setItem('access_token', res.access_token);
            if (res.organization_id) {
              localStorage.setItem('organization_id', res.organization_id);
            }
          }
        } catch (e) {
          console.error('Error setting localStorage', e);
        }
        this.router.navigate(['/crm']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Login failed. Please check your credentials.';
      }
    });
  }
}
