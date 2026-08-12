import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile, filter } from 'rxjs/operators';

@Component({
  selector: 'app-lms-author',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './lms-author.component.html',
  styleUrls: ['./lms-author.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class LmsAuthorComponent {
  private http = inject(HttpClient);

  lessonId = signal<string>('mock-lesson-id-123');
  isGenerating = signal<boolean>(false);
  progress = signal<number>(0);
  quizData = signal<any>(null);

  private pollingSub?: Subscription;

  generateAiQuiz() {
    if (!this.lessonId() || this.isGenerating()) return;

    this.isGenerating.set(true);
    this.progress.set(10);
    this.quizData.set(null);

    this.http.post<{job_id: string}>('/api/v1/lms/quizzes/generate', {
      lesson_id: this.lessonId()
    }).subscribe({
      next: (res) => {
        this.progress.set(25);
        this.pollJob(res.job_id);
      },
      error: (err) => {
        console.error('Failed to start quiz generation:', err);
        this.isGenerating.set(false);
        this.progress.set(0);
      }
    });
  }

  private pollJob(jobId: string) {
    this.pollingSub = interval(3000)
      .pipe(
        switchMap(() => this.http.get<any>(`/api/v1/ai/jobs/${jobId}`)),
        takeWhile(res => res.status !== 'completed' && res.status !== 'failed', true)
      )
      .subscribe({
        next: (res) => {
          if (res.status === 'processing' || res.status === 'pending') {
            const currentProgress = this.progress();
            if (currentProgress < 90) {
              this.progress.set(currentProgress + 15);
            }
          } else if (res.status === 'completed') {
            this.progress.set(100);
            // Simulate getting the quiz form data back
            this.quizData.set({
              title: "Generated Quiz",
              questions: [
                 { text: "Sample Question 1", answers: ["A", "B", "C"] }
              ]
            });
            this.isGenerating.set(false);
          } else if (res.status === 'failed') {
            this.isGenerating.set(false);
            this.progress.set(0);
            console.error('Job failed:', res);
          }
        },
        error: (err) => {
          console.error('Polling error:', err);
          this.isGenerating.set(false);
          this.progress.set(0);
        }
      });
  }

  ngOnDestroy() {
    if (this.pollingSub) {
      this.pollingSub.unsubscribe();
    }
  }
}
