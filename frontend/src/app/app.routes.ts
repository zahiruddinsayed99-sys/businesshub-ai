import { Routes } from '@angular/router';
import { TenantOnboardingComponent } from './features/tenant-onboarding/tenant-onboarding.component';
import { CrmPipelineComponent } from './features/crm-pipeline/crm-pipeline.component';

export const routes: Routes = [
  { path: 'onboard', component: TenantOnboardingComponent },
  { path: 'crm', component: CrmPipelineComponent },
  { path: '', redirectTo: 'onboard', pathMatch: 'full' },
];
