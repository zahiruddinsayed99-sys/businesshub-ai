import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-invite-accept',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './invite-accept.component.html',
  styleUrls: ['./invite-accept.component.scss']
})
export class InviteAcceptComponent implements OnInit {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  token: string = '';
  loading = false;
  error = '';
  success = false;

  inviteForm = this.fb.group({
    full_name: ['', Validators.required],
    password: ['', [Validators.required, Validators.minLength(8)]]
  });

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.token = params['token'] || '';
      if (!this.token) {
        this.error = 'Invalid or missing invite token.';
      }
    });
  }

  onSubmit() {
    if (this.inviteForm.invalid || !this.token) {
      return;
    }

    this.loading = true;
    this.error = '';

    const val = this.inviteForm.value;

    this.http.post(`${environment.apiUrl}/auth/invite/accept`, {
      token: this.token,
      full_name: val.full_name,
      password: val.password
    }).subscribe({
      next: () => {
        this.success = true;
        this.loading = false;

        // Show success briefly, then redirect
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 2000);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.error?.detail || 'Failed to accept invite. It may have expired.';
      }
    });
  }
}
