import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

@Pipe({
  name: 'markdown',
  standalone: true
})
export class MarkdownPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(value: string | null | undefined): SafeHtml {
    if (!value) {
      return '';
    }

    // Parse the markdown to raw HTML
    const parsedHtml = marked.parse(value) as string;

    // Sanitize the raw HTML to prevent XSS attacks
    const sanitizedHtml = DOMPurify.sanitize(parsedHtml);

    // Tell Angular we trust this HTML explicitly so it can be rendered via [innerHTML]
    return this.sanitizer.bypassSecurityTrustHtml(sanitizedHtml);
  }
}
