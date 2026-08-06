import { Routes } from '@angular/router';
import { TenantOnboardingComponent } from './features/tenant-onboarding/tenant-onboarding.component';
import { CrmPipelineComponent } from './features/crm-pipeline/crm-pipeline.component';

export const routes: Routes = [
  {
    path: 'billing',
    loadComponent: () => import('./features/billing-dashboard/billing-dashboard.component').then(m => m.BillingDashboardComponent)
  },
  { path: 'onboard', component: TenantOnboardingComponent },
  { path: 'crm', component: CrmPipelineComponent },
  {
    path: 'ai',
    loadComponent: () => import('./features/ai-platform/ai-dashboard.component').then(m => m.AiDashboardComponent)
  },
  { path: '', redirectTo: 'onboard', pathMatch: 'full' },
];
