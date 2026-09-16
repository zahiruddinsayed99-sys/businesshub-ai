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

  orgName = signal<string>('');
  companySlug = signal<string>('');

  email = signal<string>('');
  password = signal<string>('');
  fullName = signal<string>('');
  adminEmail = signal<string>('');
  adminPassword = signal<string>('');
  adminFullName = signal<string>('');
  slugEdited = signal<boolean>(false);
  isSubmitting = signal<boolean>(false);
  successMessage = signal<string | null>(null);
  errorMessage = signal<string | null>(null);

  slugify(text: string): string {
    return text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  onOrgNameChange(name: string) {
    this.orgName.set(name);
    if (!this.slugEdited()) {
      this.companySlug.set(this.slugify(name));
    }
  }

  onSlugChange(slug: string) {
    this.companySlug.set(slug);
    this.slugEdited.set(true);
  }

  createTenant() {
    if (!this.orgName() || !this.companySlug()) return;

    this.isSubmitting.set(true);
    this.successMessage.set(null);
    this.errorMessage.set(null);

    // Send the specific JSON payload with duplicated fields for backwards compatibility with the endpoint
    // "name": "string", "org_name": "string" -> Use orgName for both
    // "email": "string", "admin_email": "string" -> Use adminEmail for both
    this.http.post<any>(`${environment.apiUrl}/tenants/onboard`, {
      name: this.orgName(),
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
        this.successMessage.set(`Workspace for ${this.orgName()} created successfully!`);
        this.orgName.set('');
        this.companySlug.set('');
        this.email.set('');
        this.password.set('');
        this.fullName.set('');
        this.adminEmail.set('');
        this.adminPassword.set('');
        this.adminFullName.set('');
        this.slugEdited.set(false);
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
