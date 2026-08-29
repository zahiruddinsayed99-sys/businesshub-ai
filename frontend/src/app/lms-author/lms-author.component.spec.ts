import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { LmsAuthorComponent } from './lms-author.component';

describe('LmsAuthorComponent', () => {
  let component: LmsAuthorComponent;
  let fixture: ComponentFixture<LmsAuthorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LmsAuthorComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LmsAuthorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
