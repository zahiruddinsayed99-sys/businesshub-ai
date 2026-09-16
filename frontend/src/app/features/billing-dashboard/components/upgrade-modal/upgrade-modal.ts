import { Component, EventEmitter, Output, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../../environments/environment';

@Component({
  selector: 'app-upgrade-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './upgrade-modal.html',
  styleUrls: ['./upgrade-modal.scss']
})
export class UpgradeModalComponent {
  @Output() close = new EventEmitter<void>();
  @Output() upgradeSuccess = new EventEmitter<void>();

  private http = inject(HttpClient);
  private fb = inject(FormBuilder);

  isLoading = signal<boolean>(false);
  errorMessage = signal<string | null>(null);

  paymentForm = this.fb.group({
    cardNumber: ['', [Validators.required, Validators.pattern(/^[0-9]{16}$/)]],
    expiryDate: ['', [Validators.required, Validators.pattern(/^(0[1-9]|1[0-2])\/?([0-9]{2})$/)]],
    cvv: ['', [Validators.required, Validators.pattern(/^[0-9]{3,4}$/)]],
    nameOnCard: ['', Validators.required]
  });

  onClose() {
    this.close.emit();
  }

  onSubmit() {
    if (this.paymentForm.invalid) {
      this.paymentForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    // Simulate 2-second loading
    setTimeout(() => {
      this.http.post<{ access_token: string }>(`${environment.apiUrl}/billing/upgrade`, this.paymentForm.value)
        .subscribe({
          next: (res) => {
            if (res.access_token) {
              localStorage.setItem('access_token', res.access_token);
            }
            this.isLoading.set(false);
            this.upgradeSuccess.emit();
            this.close.emit();
          },
          error: (err) => {
            this.isLoading.set(false);
            this.errorMessage.set(err.error?.detail || 'Upgrade failed. Please try again.');
          }
        });
    }, 2000);
  }
}
