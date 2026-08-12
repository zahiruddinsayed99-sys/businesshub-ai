import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMarkdown } from 'ngx-markdown';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { LmsLearnerComponent } from './lms-learner.component';

describe('LmsLearnerComponent', () => {
  let component: LmsLearnerComponent;
  let fixture: ComponentFixture<LmsLearnerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LmsLearnerComponent, HttpClientTestingModule],
      providers: [
        provideMarkdown()
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LmsLearnerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
