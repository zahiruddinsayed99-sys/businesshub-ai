import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MarkdownPipe } from './markdown.pipe';

@Component({
  selector: 'app-lms-player',
  standalone: true,
  imports: [CommonModule, MarkdownPipe],
  template: `
    <div class="lesson-container">
      <h2>{{ title() }}</h2>

      <!-- Render the sanitized markdown securely -->
      <div class="markdown-body" [innerHTML]="content() | markdown"></div>
    </div>
  `,
  styles: [`
    .lesson-container {
      padding: 2rem;
      max-width: 800px;
      margin: 0 auto;
    }

    .markdown-body {
      line-height: 1.6;
      font-size: 1.1rem;
    }

    /* Standard Markdown Styles */
    :host ::ng-deep .markdown-body h1,
    :host ::ng-deep .markdown-body h2,
    :host ::ng-deep .markdown-body h3 {
      border-bottom: 1px solid #eaecef;
      padding-bottom: 0.3em;
      margin-top: 24px;
      margin-bottom: 16px;
    }

    :host ::ng-deep .markdown-body pre {
      background-color: #f6f8fa;
      padding: 16px;
      border-radius: 6px;
      overflow: auto;
    }

    :host ::ng-deep .markdown-body code {
      background-color: rgba(27,31,35,0.05);
      padding: 0.2em 0.4em;
      border-radius: 3px;
      font-family: monospace;
    }

    :host ::ng-deep .markdown-body blockquote {
      border-left: 4px solid #dfe2e5;
      color: #6a737d;
      padding: 0 1em;
      margin-left: 0;
    }
  `]
})
export class LmsPlayerComponent {
  // Input signals
  @Input() set lessonTitle(value: string) {
    this.title.set(value);
  }
  @Input() set lessonContent(value: string) {
    this.content.set(value);
  }

  title = signal<string>('');
  content = signal<string>('');
}
