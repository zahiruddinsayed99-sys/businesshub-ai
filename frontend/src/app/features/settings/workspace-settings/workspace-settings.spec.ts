import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';

import { WorkspaceSettings } from './workspace-settings';

describe('WorkspaceSettings', () => {
  let component: WorkspaceSettings;
  let fixture: ComponentFixture<WorkspaceSettings>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkspaceSettings],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkspaceSettings);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
