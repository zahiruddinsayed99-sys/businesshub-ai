import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { LmsAuthorComponent } from './lms-author.component';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

describe('LmsAuthorComponent', () => {
  let component: LmsAuthorComponent;
  let fixture: ComponentFixture<LmsAuthorComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LmsAuthorComponent, FormsModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    }).compileComponents();

    fixture = TestBed.createComponent(LmsAuthorComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start generation, poll, and update quiz data on completion', fakeAsync(() => {
    component.generateAiQuiz();

    const startReq = httpMock.expectOne('/api/v1/lms/quizzes/generate');
    expect(startReq.request.method).toBe('POST');
    startReq.flush({ job_id: 'job123' });

    expect(component.isGenerating()).toBeTrue();
    expect(component.progress()).toBe(25);

    // First poll (processing)
    tick(3000);
    const pollReq1 = httpMock.expectOne('/api/v1/ai/jobs/job123');
    pollReq1.flush({ status: 'processing' });
    expect(component.progress()).toBe(40);

    // Second poll (completed)
    tick(3000);
    const pollReq2 = httpMock.expectOne('/api/v1/ai/jobs/job123');
    pollReq2.flush({ status: 'completed' });

    expect(component.isGenerating()).toBeFalse();
    expect(component.progress()).toBe(100);
    expect(component.quizData()?.title).toBe('Generated Quiz');

    // Ensure no more polling
    tick(3000);
    httpMock.expectNone('/api/v1/ai/jobs/job123');
  }));

  it('should handle API errors and stop polling', fakeAsync(() => {
     component.generateAiQuiz();

    const startReq = httpMock.expectOne('/api/v1/lms/quizzes/generate');
    startReq.flush({ job_id: 'job123' });

    // Poll -> Error
    tick(3000);
    const pollReq1 = httpMock.expectOne('/api/v1/ai/jobs/job123');
    pollReq1.error(new ProgressEvent('error'));

    expect(component.isGenerating()).toBeFalse();
    expect(component.progress()).toBe(0);

    // Ensure no more polling
    tick(3000);
    httpMock.expectNone('/api/v1/ai/jobs/job123');
  }));
});
