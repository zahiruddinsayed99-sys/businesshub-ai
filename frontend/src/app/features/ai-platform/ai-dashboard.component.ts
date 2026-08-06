import { Component, ChangeDetectionStrategy, signal, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Subject, interval, Subscription } from 'rxjs';
import { switchMap, takeWhile, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-ai-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './ai-dashboard.component.html',
  styleUrls: ['./ai-dashboard.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AiDashboardComponent implements OnDestroy {
  uploadForm;

  jobId = signal<string | null>(null);
  jobStatus = signal<string | null>(null);
  jobProgress = signal<number>(0);

  private pollingSubscription?: Subscription;

  constructor(private fb: FormBuilder, private http: HttpClient) {
    this.uploadForm = this.fb.group({
      title: ['', Validators.required],
      content: ['', Validators.required]
    });
  }

  onUpload() {
    if (this.uploadForm.invalid) return;

    const payload = this.uploadForm.value;

    // Assume Tenant interceptor attaches auth and X-Organization-Id
    this.http.post<{job_id: string}>(`${environment.apiUrl}/ai/documents/upload`, payload)
      .pipe(
        catchError(err => {
          console.error(err);
          this.jobStatus.set('FAILED_TO_UPLOAD');
          return of(null);
        })
      )
      .subscribe(res => {
        if (res && res.job_id) {
          this.jobId.set(res.job_id);
          this.jobStatus.set('PENDING');
          this.jobProgress.set(10);
          this.startPolling(res.job_id);
        }
      });
  }

  private startPolling(jobId: string) {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }

    this.pollingSubscription = interval(2000)
      .pipe(
        switchMap(() => this.http.get<{status: string, result: any}>(`${environment.apiUrl}/ai/jobs/${jobId}`)),
        takeWhile(res => res.status !== 'SUCCESS' && res.status !== 'FAILURE', true),
        catchError(err => {
          console.error(err);
          return of({status: 'FAILURE', result: null});
        })
      )
      .subscribe(res => {
        this.jobStatus.set(res.status);
        if (res.status === 'SUCCESS') {
          this.jobProgress.set(100);
        } else if (res.status === 'FAILURE') {
          this.jobProgress.set(0);
        } else {
          // just simulating progress for pending state
          this.jobProgress.update(p => p < 90 ? p + 10 : 90);
        }
      });
  }

  ngOnDestroy() {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }
  }
}
