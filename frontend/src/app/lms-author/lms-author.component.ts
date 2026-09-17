import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { interval, Subscription, of } from 'rxjs';
import { switchMap, takeWhile, catchError, take } from 'rxjs/operators';
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


  publishCourse(id?: string) {
    // Fallback to the component's signal if no ID is passed from the template
    const targetId = id || this.courseId();
    if (!targetId) return;

    this.http.patch<any>(`${environment.apiUrl}/lms/courses/${targetId}/status`, {}).subscribe({
      next: (res) => {
        alert('Course published successfully!');
        this.loadCourses(); // Crucial: refreshes the UI after state change
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

    // 1. Fire the generation with the required Pydantic body payload
    this.http.post<any>(`${environment.apiUrl}/lms/lessons/${this.lessonId()}/quiz`, {
      lesson_id: this.lessonId()
    }).subscribe({
      next: () => {
        this.progress.set(25);
        // 2. Poll the quiz endpoint directly
        this.pollQuizCompletion(this.lessonId());
      },
      error: (err) => {
        console.error('Failed to start quiz generation:', err);
        this.isGenerating.set(false);
        this.progress.set(0);
      }
    });
  }

  private pollQuizCompletion(lessonId: string) {
    const maxAttempts = 20; // 60 seconds total at 3s intervals

    this.pollingSub = interval(3000)
      .pipe(
        take(maxAttempts), // Automatically stop the interval after 20 tries
        switchMap(() =>
          this.http.get<any>(`${environment.apiUrl}/lms/lessons/${lessonId}/quiz`).pipe(
            catchError(err => {
              if (err.status === 404) return of(null);
              throw err;
            })
          )
        ),
        takeWhile(res => res === null, true)
      )
      .subscribe({
        next: (res) => {
          if (res === null) {
            const currentProgress = this.progress();
            if (currentProgress < 90) {
              this.progress.set(currentProgress + 15);
            }
          } else {
            // Success!
            this.progress.set(100);
            this.quizData.set(res);
            this.isGenerating.set(false);
          }
        },
        error: (err) => {
          console.error('Polling error:', err);
          this.isGenerating.set(false);
          this.progress.set(0);
        },
        complete: () => {
          // If the observable completes but we are still in a generating state, it means we hit the maxAttempts limit
          if (this.isGenerating()) {
            this.isGenerating.set(false);
            this.progress.set(0);
            alert("Quiz generation timed out. The AI task likely failed on the server.");
          }
        }
      });
  }

  ngOnDestroy() {
    if (this.pollingSub) {
      this.pollingSub.unsubscribe();
    }
  }
}
