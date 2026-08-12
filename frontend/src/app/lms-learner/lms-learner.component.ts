import { Component, ChangeDetectionStrategy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MarkdownModule } from 'ngx-markdown';

@Component({
  selector: 'app-lms-learner',
  standalone: true,
  imports: [CommonModule, MarkdownModule],
  templateUrl: './lms-learner.component.html',
  styleUrls: ['./lms-learner.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class LmsLearnerComponent {
  // Mock data for the dashboard
  activeEnrollment = signal<any>({
    courseTitle: 'Advanced Angular Architecture',
    progressPercent: 45,
    status: 'ENROLLED',
    warning: 'Low Quiz Score (65%)'
  });

  lessonMarkdown = signal<string>(`
# Module 1: Signals
Welcome to the lesson.

\`\`\`typescript
const mySignal = signal(0);
console.log(mySignal());
\`\`\`

- [x] Step 1
- [ ] Step 2
  `);
}
