import { Routes } from '@angular/router';
import { TenantOnboardingComponent } from './features/tenant-onboarding/tenant-onboarding.component';

export const routes: Routes = [
  { path: 'onboard', component: TenantOnboardingComponent },
  { path: '', redirectTo: 'onboard', pathMatch: 'full' },
];
