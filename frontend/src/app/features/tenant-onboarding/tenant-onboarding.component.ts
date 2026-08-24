import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { TenantService, TenantOnboardResponse } from '../../core/services/tenant.service';
import { Router, ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-tenant-onboarding',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './tenant-onboarding.component.html',
  styleUrl: './tenant-onboarding.component.scss',
})
export class TenantOnboardingComponent implements OnInit {
  onboardingForm!: FormGroup;
  isSubmitting = false;
  errorMessage: string | null = null;
  onboardingSuccess: TenantOnboardResponse | null = null;

  inviteCode: string | null = null;

  isCheckingSlug = false;
  isSlugAvailable: boolean | null = null;
  slugSubject = new Subject<string>();

  constructor(
    private fb: FormBuilder,
    private tenantService: TenantService,
    private router: Router,
    private route: ActivatedRoute
  ) { }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      this.inviteCode = params['code'] || null;
    });

    this.onboardingForm = this.fb.group({
      org_name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(255)]],
      slug: ['', [Validators.pattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]],
      admin_full_name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(255)]],
      admin_email: ['', [Validators.required, Validators.email]],
      admin_password: ['', [Validators.required, Validators.minLength(8)]],
    });

    // Auto-generate slug from organization name if slug field is untouched
    this.onboardingForm.get('org_name')?.valueChanges.subscribe((name) => {
      const slugControl = this.onboardingForm.get('slug');
      if (slugControl && !slugControl.dirty) {
        const generated = this.slugify(name);
        slugControl.setValue(generated, { emitEvent: false });
        if (generated.length >= 2) {
          this.slugSubject.next(generated);
        }
      }
    });

    // Real-time slug availability debounce handler
    this.slugSubject
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap((slug) => {
          if (!slug || slug.length < 2) {
            this.isCheckingSlug = false;
            this.isSlugAvailable = null;
            return [];
          }
          this.isCheckingSlug = true;
          this.isSlugAvailable = null;
          return this.tenantService.checkSlugAvailability(slug);
        })
      )
      .subscribe({
        next: (res) => {
          this.isCheckingSlug = false;
          this.isSlugAvailable = res.available;
        },
        error: () => {
          this.isCheckingSlug = false;
          this.isSlugAvailable = null;
        },
      });
  }

  onSlugInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const slug = this.slugify(input.value);
    this.onboardingForm.get('slug')?.setValue(slug, { emitEvent: false });
    this.slugSubject.next(slug);
  }

  slugify(text: string): string {
    return text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  getPasswordStrength(): { score: number; label: string; color: string } {
    const pwd = this.onboardingForm.get('admin_password')?.value || '';
    if (!pwd) return { score: 0, label: 'None', color: '#4a5568' };
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;

    if (score <= 1) return { score: 25, label: 'Weak', color: '#ef4444' };
    if (score === 2) return { score: 50, label: 'Fair', color: '#f59e0b' };
    if (score === 3) return { score: 75, label: 'Good', color: '#3b82f6' };
    return { score: 100, label: 'Strong', color: '#10b981' };
  }

  onSubmit(): void {
    if (this.onboardingForm.invalid || !this.inviteCode) {
      this.onboardingForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = null;

    const formValues = this.onboardingForm.value;
    const payload = {
      org_name: formValues.org_name,
      slug: formValues.slug || undefined,
      admin_email: formValues.admin_email,
      admin_password: formValues.admin_password,
      admin_full_name: formValues.admin_full_name,
      invite_code: this.inviteCode
    };

    this.tenantService.onboardTenant(payload).subscribe({
      next: (res) => {
        this.isSubmitting = false;
        this.onboardingSuccess = res;
      },
      error: (err) => {
        this.isSubmitting = false;
        if (err.error && err.error.detail) {
          this.errorMessage = typeof err.error.detail === 'string' ? err.error.detail : err.error.detail.detail || 'Onboarding failed';
        } else {
          this.errorMessage = 'An unexpected error occurred during onboarding.';
        }
      },
    });
  }
  goToBilling() {
    if (this.onboardingSuccess && this.onboardingSuccess.access_token) {
      // 1. Save the token so the app knows the user is logged in
      localStorage.setItem('access_token', this.onboardingSuccess.access_token);
      if (this.onboardingSuccess.organization_id) {
        localStorage.setItem('organization_id', this.onboardingSuccess.organization_id);
      }
      // 2. Clear the success state
      this.onboardingSuccess = null;
      // 3. Navigate to the billing dashboard
      this.router.navigate(['/billing']);
    }
  }
}
