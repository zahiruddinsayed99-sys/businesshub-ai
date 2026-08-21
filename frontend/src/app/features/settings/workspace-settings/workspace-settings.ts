import { Component, ChangeDetectionStrategy, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-workspace-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './workspace-settings.html',
  styleUrls: ['./workspace-settings.scss']
})
export class WorkspaceSettings {
  private http = inject(HttpClient);
  private fb = inject(FormBuilder);

  showSuccessToast = signal<boolean>(false);

  companyForm = this.fb.group({
    name: ['', Validators.required],
    gstin: ['', [Validators.required, Validators.pattern(/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/)]],
    billing_state: ['', Validators.required]
  });

  inviteEmail = signal<string>('');
  inviteLink = signal<string>('');

  constructor() {
    this.loadCompanyDetails();
  }

  loadCompanyDetails() {
    this.http.get<any>('/api/v1/organizations/me').subscribe({
      next: (res) => {
        this.companyForm.patchValue({
          name: res.name || '',
          gstin: res.gstin || '',
          billing_state: res.billing_state || ''
        });
      },
      error: (err) => {
        console.error('Failed to load company details', err);
      }
    });
  }

  saveCompanyDetails() {
    if (this.companyForm.valid) {
      this.http.patch('/api/v1/organizations/me', this.companyForm.value).subscribe({
        next: () => {
          this.showSuccessToast.set(true);
          setTimeout(() => this.showSuccessToast.set(false), 3000);
        },
        error: (err) => {
          console.error('Failed to save company details', err);
        }
      });
    }
  }

  createInvite() {
    if (!this.inviteEmail()) {
      return;
    }

    this.http.post<{token: string}>('/api/v1/organizations/invitations', { email: this.inviteEmail() }).subscribe({
      next: (res) => {
        const fullUrl = `${window.location.origin}/invite/accept?token=${res.token}`;
        this.inviteLink.set(fullUrl);
      },
      error: (err) => {
        console.error('Failed to create invite', err);
      }
    });
  }

  copyInviteLink() {
    if (this.inviteLink()) {
      navigator.clipboard.writeText(this.inviteLink()).then(() => {
        console.log('Copied to clipboard');
      }).catch(err => {
        console.error('Failed to copy', err);
      });
    }
  }
}
