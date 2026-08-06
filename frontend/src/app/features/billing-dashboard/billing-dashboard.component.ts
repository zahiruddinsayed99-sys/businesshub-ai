import { Component, ChangeDetectionStrategy, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

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

  loadBillingInfo() {
    this.http.get<any>('/api/v1/organizations/me').subscribe(res => {
      this.subscriptionTier.set(res.subscription_tier || 'FREE');
      this.activePlanStatus.set(res.subscription_status || 'INACTIVE');
      this.creditsUsed.set(res.ai_credits_used || 0);
      this.creditsMax.set(100 + (res.bonus_ai_credits || 0));
      this.seatsUsed.set(res.user_count || 1);
      this.seatsMax.set(3);

      if (this.subscriptionTier() === 'FREE' && this.seatsUsed() > this.seatsMax()) {
        this.isSoftLocked.set(true);
      }
    });
  }

  saveGstin() {
    if (this.gstinForm.valid) {
      this.http.patch('/api/v1/organizations/me', this.gstinForm.value).subscribe();
    }
  }

  onCheckout() {
    this.http.post<{url: string}>('/api/v1/billing/checkout', {}).subscribe(res => {
      window.location.href = res.url;
    });
  }

  onCustomerPortal() {
    this.http.post<{url: string}>('/api/v1/billing/portal', {}).subscribe(res => {
      window.location.href = res.url;
    });
  }
}
