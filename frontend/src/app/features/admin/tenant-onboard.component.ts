import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-admin-tenant-onboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './tenant-onboard.component.html',
  styleUrls: ['./tenant-onboard.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TenantOnboardComponent {
  private http = inject(HttpClient);

  companyName = signal<string>('');
  orgName = signal<string>('');
  companySlug = signal<string>('');
  email = signal<string>('');
  adminEmail = signal<string>('');
  password = signal<string>('');
  adminPassword = signal<string>('');
  fullName = signal<string>('');
  adminFullName = signal<string>('');

  isSubmitting = signal<boolean>(false);
  successMessage = signal<string | null>(null);
  errorMessage = signal<string | null>(null);

  createTenant() {
    if (!this.companyName() || !this.companySlug()) return;

    this.isSubmitting.set(true);
    this.successMessage.set(null);
    this.errorMessage.set(null);

    this.http.post<any>(`${environment.apiUrl}/tenants/onboard`, {
      name: this.companyName(),
      org_name: this.orgName(),
      slug: this.companySlug(),
      email: this.email(),
      admin_email: this.adminEmail(),
      password: this.password(),
      admin_password: this.adminPassword(),
      full_name: this.fullName(),
      admin_full_name: this.adminFullName()
    }).subscribe({
      next: (res) => {
        this.successMessage.set(`Workspace for ${this.companyName()} created successfully!`);
        this.companyName.set('');
        this.companySlug.set('');
        this.isSubmitting.set(false);
      },
      error: (err) => {
        if (err.status === 409) {
          this.errorMessage.set('Workspace or Email already exists');
        } else {
          this.errorMessage.set(err.error?.detail || 'Failed to create workspace');
        }
        this.isSubmitting.set(false);
      }
    });
  }
}
