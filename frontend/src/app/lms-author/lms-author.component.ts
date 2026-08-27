import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';
import { environment } from '../../environments/environment';

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

  // Courses list
  courses = signal<any[]>([]);

  // Course variables
  courseTitle = signal<string>('');
  courseDescription = signal<string>('');
  courseId = signal<string>('');

  ngOnInit() {
    this.loadCourses();
  }

  loadCourses() {
    this.http.get<any[]>(`${environment.apiUrl}/lms/courses`).subscribe({
      next: (res) => {
        this.courses.set(res);
      },
      error: (err) => console.error('Failed to load courses:', err)
    });
  }

  selectedCourseDetail = signal<any>(null);

  selectCourse(id: string) {
    this.courseId.set(id);
    this.moduleId.set('');
    this.lessonId.set('');
    this.http.get<any>(`${environment.apiUrl}/lms/courses/${id}`).subscribe({
      next: (res) => {
        this.selectedCourseDetail.set(res);
      },
      error: (err) => console.error('Failed to get course details:', err)
    });
  }

  selectModule(id: string) {
    this.moduleId.set(id);
    this.lessonId.set('');
  }

  selectLesson(id: string) {
    this.lessonId.set(id);
  }

  publishCourse(id: string) {
    this.http.patch<any>(`${environment.apiUrl}/lms/courses/${id}/status`, {}).subscribe({
      next: (res) => {
        alert('Course published successfully');
        this.loadCourses();
      },
      error: (err) => console.error('Failed to publish course:', err)
    });
  }

  // Module variables
  moduleTitle = signal<string>('');
  moduleDescription = signal<string>('');
  moduleId = signal<string>('');

  // Lesson variables
  lessonTitle = signal<string>('');
  lessonContentBody = signal<string>('');
  lessonId = signal<string>('');

  // Quiz generation
  isGenerating = signal<boolean>(false);
  progress = signal<number>(0);
  quizData = signal<any>(null);

  private pollingSub?: Subscription;

  createCourse() {
    this.http.post<any>(`${environment.apiUrl}/lms/courses`, {
      title: this.courseTitle(),
      description: this.courseDescription()
    }).subscribe({
      next: (res) => {
        this.courseId.set(res.id);
        alert('Course created successfully');
        this.loadCourses();
      },
      error: (err) => console.error('Failed to create course:', err)
    });
  }


  publishCourse() {
    if (!this.courseId()) return;
    this.http.patch<any>(`${environment.apiUrl}/lms/courses/${this.courseId()}/status`, {}).subscribe({
      next: (res) => {
        alert('Course published successfully!');
      },
      error: (err) => console.error('Failed to publish course:', err)
    });
  }

  createModule() {
    if (!this.courseId()) return;
    this.http.post<any>(`${environment.apiUrl}/lms/courses/${this.courseId()}/modules`, {
      title: this.moduleTitle(),
      description: this.moduleDescription(),
      order_index: 1
    }).subscribe({
      next: (res) => {
        this.moduleId.set(res.id);
        alert('Module created successfully');
        if (this.courseId()) {
          this.selectCourse(this.courseId());
        }
      },
      error: (err) => console.error('Failed to create module:', err)
    });
  }

  createLesson() {
    if (!this.moduleId()) return;
    this.http.post<any>(`${environment.apiUrl}/lms/modules/${this.moduleId()}/lessons`, {
      title: this.lessonTitle(),
      content_body: this.lessonContentBody(),
      order_index: 1
    }).subscribe({
      next: (res) => {
        this.lessonId.set(res.id);
        alert('Lesson created successfully');
        if (this.courseId()) {
          this.selectCourse(this.courseId());
        }
      },
      error: (err) => console.error('Failed to create lesson:', err)
    });
  }

  generateAiQuiz() {
    if (!this.lessonId() || this.isGenerating()) return;

    this.isGenerating.set(true);
    this.progress.set(10);
    this.quizData.set(null);

    this.http.post<{ job_id: string }>(`${environment.apiUrl}/lms/lessons/${this.lessonId()}/quiz`, {
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
        switchMap(() => this.http.get<any>(`${environment.apiUrl}/ai/jobs/${jobId}`)),
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
            this.quizData.set(res.result || {
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
