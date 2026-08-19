import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { MarkdownModule, MarkdownService } from 'ngx-markdown';

// We'll import LmsAuthorComponent to test real components for LMS markdown.
import { LmsAuthorComponent } from './lms-author/lms-author.component';
import { CrmDealService } from './features/crm-pipeline/crm-deal.service';

describe('Tier 1 Unit Tests (Frontend)', () => {
  let dealService: CrmDealService;
  let httpTestingController: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [CrmDealService]
    });
    dealService = TestBed.inject(CrmDealService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  describe('CRM Kanban Card State Changes', () => {
    it('should correctly update the stage of a Kanban card via CrmDealService', () => {
      const dealId = '123';
      const newStage = 'QUALIFIED';

      dealService.updateDealStage(dealId, newStage).subscribe((res: any) => {
        expect(res.stage).toBe('QUALIFIED');
      });

      const req = httpTestingController.expectOne(`/api/v1/crm/deals/${dealId}/stage`);
      expect(req.request.method).toEqual('PATCH');
      expect(req.request.body).toEqual({ stage: newStage });

      req.flush({ id: dealId, stage: 'QUALIFIED' });
    });
  });

  describe('API Error Handling Gracefully', () => {
    it('should handle ERR_VALIDATION_001 gracefully from CrmDealService', () => {
      const apiErrorResponse = {
        code: 'ERR_VALIDATION_001',
        detail: [{ msg: 'value is not a valid email address' }]
      };

      dealService.updateDealStage('123', 'QUALIFIED').subscribe({
        next: () => fail('should have failed with the 422 error'),
        error: (error: any) => {
          expect(error.status).toEqual(422);
          expect(error.error.code).toEqual('ERR_VALIDATION_001');
        }
      });

      const req = httpTestingController.expectOne('/api/v1/crm/deals/123/stage');
      req.flush(apiErrorResponse, { status: 422, statusText: 'Unprocessable Entity' });
    });
  });

});

describe('Tier 1 Unit Tests (Frontend) - Components', () => {
  let fixture: ComponentFixture<LmsAuthorComponent>;
  let component: LmsAuthorComponent;
  let markdownService: MarkdownService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LmsAuthorComponent, MarkdownModule.forRoot(), HttpClientTestingModule],
      providers: []
    }).compileComponents();

    fixture = TestBed.createComponent(LmsAuthorComponent);
    component = fixture.componentInstance;
    markdownService = TestBed.inject(MarkdownService);
    fixture.detectChanges();
  });

  describe('LMS Markdown Parser Security (XSS Prevention)', () => {
    it('should sanitize script tags from markdown content using ngx-markdown', () => {
      const maliciousMarkdown = '# Hello\n\n<script>alert("XSS")</script>\n[link](javascript:alert("XSS"))';

      const compiled = markdownService.parse(maliciousMarkdown);

      expect(compiled).not.toContain('<script>alert');
    });
  });
});
