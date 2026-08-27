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
  }

  private http = inject(HttpClient);

  availableCourses = signal<any[]>([
    { id: 'mock-course-1', title: 'Advanced Angular Architecture', description: 'Learn advanced topics.' }
  ]);

  activeEnrollment = signal<any>(null);
  lessonMarkdown = signal<string>('');

  quizData = signal<any>(null);
  selectedAnswers = signal<any>({});
  quizResult = signal<any>(null);

  enrollCourse(courseId: string) {
    this.http.post<any>(`${environment.apiUrl}/lms/enrollments`, { course_id: courseId }).subscribe({
      next: (res) => {
        this.activeEnrollment.set({
          courseTitle: 'Advanced Angular Architecture',
          progressPercent: 0,
          status: 'ENROLLED',
          warning: null
        });

        // Mock lesson content for now
        this.lessonMarkdown.set(`
# Module 1: Signals
Welcome to the lesson.

\`\`\`typescript
const mySignal = signal(0);
console.log(mySignal());
\`\`\`

- [x] Step 1
- [ ] Step 2
        `);
      },
      error: (err) => console.error('Enrollment failed:', err)
    });
  }

  takeQuiz() {
    this.quizData.set({
      id: 'mock-quiz-1',
      questions: [
        { text: "What is 1+1?", answers: ["1", "2", "3", "4"] },
        { text: "What is 2+2?", answers: ["2", "3", "4", "5"] },
        { text: "What is 3+3?", answers: ["3", "4", "6", "8"] },
        { text: "What is 4+4?", answers: ["4", "6", "8", "10"] },
        { text: "What is 5+5?", answers: ["5", "8", "10", "12"] },
      ]
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
    const answersArray = Object.keys(this.selectedAnswers()).map(index => ({
      question_id: `q${index}`,
      selected_option_id: this.selectedAnswers()[index]
    }));

    this.http.post<any>(`${environment.apiUrl}/lms/quizzes/attempts`, {
      quiz_id: this.quizData().id,
      responses: answersArray
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
