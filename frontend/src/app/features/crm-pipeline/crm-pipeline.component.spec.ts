import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { CrmPipelineComponent } from './crm-pipeline.component';
import { CrmDealService } from './crm-deal.service';
import { CrmAiService } from './crm-ai.service';
import { of, throwError } from 'rxjs';
import { DragDropModule, CdkDragDrop } from '@angular/cdk/drag-drop';
import { CrmDeal } from './crm-deal.model';

describe('CrmPipelineComponent', () => {
  let component: CrmPipelineComponent;
  let fixture: ComponentFixture<CrmPipelineComponent>;
  let mockCrmDealService: any;
  let mockCrmAiService: any;

  beforeEach(async () => {
    mockCrmDealService = {
      getDeals: jasmine.createSpy('getDeals').and.returnValue(of([])),
      updateDealStage: jasmine.createSpy('updateDealStage').and.returnValue(of({}))
    };

    mockCrmAiService = {
      scoreDeal: jasmine.createSpy('scoreDeal').and.returnValue(of({ job_id: '123' })),
      getJobStatus: jasmine.createSpy('getJobStatus').and.returnValue(of({ status: 'SUCCESS', result: { status: 'completed' } })),
      draftFollowUp: jasmine.createSpy('draftFollowUp').and.returnValue(of({ draft: 'Test Draft' }))
    };

    await TestBed.configureTestingModule({
      imports: [CrmPipelineComponent, DragDropModule],
      providers: [
        { provide: CrmDealService, useValue: mockCrmDealService },
        { provide: CrmAiService, useValue: mockCrmAiService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CrmPipelineComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should handle drop event optimistically and rollback on failure', fakeAsync(() => {
    const deal: CrmDeal = { id: '1', title: 'Deal 1', stage: 'LEAD', value_amount: 100, organization_id: 'org1' };
    component.deals.set([deal]);

    const event = {
      previousContainer: { data: [deal] },
      container: { data: [] },
      previousIndex: 0,
      currentIndex: 0
    } as unknown as CdkDragDrop<CrmDeal[]>;

    mockCrmDealService.updateDealStage.and.returnValue(throwError(() => new Error('API Error')));

    component.drop(event, 'WON');

    // Check optimistic update
    expect(component.deals()[0].stage).toBe('WON');

    tick(300); // Wait for debounce

    // Check rollback
    expect(component.deals()[0].stage).toBe('LEAD');
    expect(component.errorToast()).toBe('Failed to update deal stage. Rolled back.');

    tick(3000); // clear toast
  }));
});
