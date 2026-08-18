import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LmsPlayerComponent } from './lms-player.component';
import { MarkdownPipe } from './markdown.pipe';

describe('LmsPlayerComponent', () => {
  let component: LmsPlayerComponent;
  let fixture: ComponentFixture<LmsPlayerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LmsPlayerComponent, MarkdownPipe]
    }).compileComponents();

    fixture = TestBed.createComponent(LmsPlayerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render lesson title and sanitized content', () => {
    component.lessonTitle = 'Test Lesson';
    component.lessonContent = '# Heading\n<script>alert("xss")</script>';
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h2')?.textContent).toContain('Test Lesson');
    expect(compiled.querySelector('.markdown-body')?.innerHTML).toContain('Heading');
    expect(compiled.querySelector('.markdown-body')?.innerHTML).not.toContain('<script>');
  });
});
