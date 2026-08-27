import { Component, ChangeDetectionStrategy, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MarkdownModule } from 'ngx-markdown';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-lms-learner',
  standalone: true,
  imports: [CommonModule, MarkdownModule, FormsModule],
  templateUrl: './lms-learner.component.html',
  styleUrls: ['./lms-learner.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class LmsLearnerComponent implements OnInit {

  ngOnInit() {
    this.http.get<any[]>(`${environment.apiUrl}/lms/courses`).subscribe({
      next: (res) => this.availableCourses.set(res),
      error: (err) => console.error('Failed to load courses:', err)
    });
    this.loadAvailableCourses();
    this.loadEnrollments();
  }

  private http = inject(HttpClient);

  availableCourses = signal<any[]>([]);
  enrollments = signal<any[]>([]);

  activeEnrollment = signal<any>(null);
  enrolledCourseDetail = signal<any>(null);
  activeLesson = signal<any>(null);
  lessonProgresses = signal<any[]>([]);

  quizData = signal<any>(null);
  selectedAnswers = signal<any>({});
  quizResult = signal<any>(null);

  loadAvailableCourses() {
    this.http.get<any[]>(`${environment.apiUrl}/lms/courses`).subscribe({
      next: (res) => this.availableCourses.set(res),
      error: (err) => console.error('Failed to load courses:', err)
    });
  }

  loadEnrollments() {
    this.http.get<any[]>(`${environment.apiUrl}/lms/enrollments`).subscribe({
      next: (res) => this.enrollments.set(res),
      error: (err) => console.error('Failed to load enrollments:', err)
    });
  }

  isEnrolled(courseId: string) {
    return this.enrollments().some(e => e.course_id === courseId);
  }

  enrollCourse(courseId: string) {
    this.http.post<any>(`${environment.apiUrl}/lms/enrollments`, { course_id: courseId }).subscribe({
      next: (res) => {
        alert('Enrolled successfully!');
        this.loadEnrollments();
      },
      error: (err) => console.error('Enrollment failed:', err)
    });
  }

  openCourse(courseId: string) {
    this.http.get<any>(`${environment.apiUrl}/lms/courses/${courseId}`).subscribe({
      next: (res) => {
        this.enrolledCourseDetail.set(res);
        const enrollment = this.enrollments().find(e => e.course_id === courseId);
        if (enrollment) {
          this.activeEnrollment.set({
            ...enrollment,
            courseTitle: res.title
          });
        }
        this.loadProgress(courseId);
        this.activeLesson.set(null);
        this.quizData.set(null);
        this.quizResult.set(null);
      },
      error: (err) => console.error('Failed to load course details:', err)
    });
  }

  loadProgress(courseId: string) {
    this.http.get<any[]>(`${environment.apiUrl}/lms/courses/${courseId}/progress`).subscribe({
      next: (res) => this.lessonProgresses.set(res),
      error: (err) => console.error('Failed to load progress:', err)
    });
  }

  viewLesson(lesson: any) {
    this.activeLesson.set(lesson);
    this.quizData.set(null);
    this.quizResult.set(null);
  }

  markLessonComplete(lessonId: string) {
    this.http.post<any>(`${environment.apiUrl}/lms/lessons/${lessonId}/progress`, { is_completed: true }).subscribe({
      next: (res) => {
        this.loadProgress(this.enrolledCourseDetail().id);
        alert('Lesson marked complete');
      },
      error: (err) => console.error('Failed to mark lesson complete:', err)
    });
  }

  takeQuiz(lessonId: string) {
    this.http.get<any>(`${environment.apiUrl}/lms/lessons/${lessonId}/quiz`).subscribe({
      next: (res) => {
        this.quizData.set(res);
        this.selectedAnswers.set({});
        this.quizResult.set(null);
      },
      error: (err) => {
        console.error('Failed to load quiz:', err);
        alert('No quiz available for this lesson.');
      }
    });
  }

  selectAnswer(questionIndex: number, answer: string) {
    const current = this.selectedAnswers();
    current[questionIndex] = answer;
    this.selectedAnswers.set({ ...current });
  }

  submitQuiz() {
    if (!this.quizData()) return;

    // Convert selected answers map to the expected backend format
    const answersObj = this.selectedAnswers();
    const responsesMap: { [key: string]: string } = {};
    Object.keys(answersObj).forEach(qId => {
      responsesMap[qId] = answersObj[qId];
    });

    this.http.post<any>(`${environment.apiUrl}/lms/quizzes/attempts?quiz_id=${this.quizData().id}`, {
      responses: responsesMap
    }).subscribe({
      next: (res) => {
        // Enforce BR-LMS-001 in UI based on score read from backend
        // Actually, backend should return 'passed', but we double check or use it
        this.quizResult.set({
          score: res.score,
          passed: res.score >= 80
        });
        this.quizData.set(null);
      },
      error: (err) => console.error('Quiz submission failed:', err)
    });
  }
}
