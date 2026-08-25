import { Component, ChangeDetectionStrategy, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-billing-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './billing-dashboard.component.html',
  styleUrls: ['./billing-dashboard.component.scss']
})
export class BillingDashboardComponent {
  private http = inject(HttpClient);
  private fb = inject(FormBuilder);

  subscriptionTier = signal<string>('FREE');
  activePlanStatus = signal<string>('INACTIVE');
  seatsUsed = signal<number>(3);
  seatsMax = signal<number>(3);
  creditsUsed = signal<number>(50);
  creditsMax = signal<number>(100);
  isSoftLocked = signal<boolean>(false);

  gstinForm = this.fb.group({
    gstin: ['', [Validators.required, Validators.pattern(/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/)]],
    billingState: ['', Validators.required]
  });

  constructor() {
    this.loadBillingInfo();
  }

  successToast = signal<boolean>(false);

  loadBillingInfo() {
    this.http.get<any>(`${environment.apiUrl}/organizations/me`).subscribe(res => {
      this.subscriptionTier.set(res.subscription_tier || 'FREE');
      this.activePlanStatus.set(res.subscription_status || 'INACTIVE');
      this.creditsUsed.set(res.ai_credits_used || 0);
      this.creditsMax.set(100 + (res.bonus_ai_credits || 0));
      this.seatsUsed.set(res.user_count || 1);
      this.seatsMax.set(3);

      this.gstinForm.patchValue({
        gstin: res.gstin || '',
        billingState: res.billing_state || ''
      });

      if (this.subscriptionTier() === 'FREE' && this.seatsUsed() > this.seatsMax()) {
        this.isSoftLocked.set(true);
      }
    });
  }

  saveGstin() {
    if (this.gstinForm.valid) {
      this.http.patch(`${environment.apiUrl}/organizations/me`, {
        gstin: this.gstinForm.value.gstin,
        billing_state: this.gstinForm.value.billingState
      }).subscribe({
        next: () => {
          this.successToast.set(true);
          setTimeout(() => this.successToast.set(false), 3000);
        }
      });
    }
  }

  onCheckout() {
    this.http.post<{ url: string }>(`${environment.apiUrl}/billing/checkout`, {}).subscribe({
      next: (response) => {
        if (response.url) {
          window.location.href = response.url; // Manually route to Stripe
        }
      }
    });
  }

  onCustomerPortal() {
    this.http.post<{ url: string }>(`${environment.apiUrl}/billing/portal`, {}).subscribe({
      next: (response) => {
        if (response.url) {
          window.location.href = response.url; // Manually route to Stripe
        }
      }
    });
  }
}
