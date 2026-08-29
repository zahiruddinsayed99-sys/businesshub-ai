import { Routes } from '@angular/router';
import { TenantOnboardingComponent } from './features/tenant-onboarding/tenant-onboarding.component';
import { CrmPipelineComponent } from './features/crm-pipeline/crm-pipeline.component';
import { MainLayoutComponent } from './core/layout/main-layout/main-layout.component';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';
import { superAdminGuard } from './core/guards/super-admin.guard';
import { lmsAuthorGuard } from './core/guards/lms-author.guard';
import { LoginComponent } from './features/auth/login/login.component';
import { InviteAcceptComponent } from './features/auth/invite-accept/invite-accept.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'invite/accept', component: InviteAcceptComponent },
  { path: 'onboard', component: TenantOnboardingComponent },
  {
    path: '',
    component: MainLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: 'crm', component: CrmPipelineComponent },
      {
        path: 'ai',
        loadComponent: () => import('./features/ai-platform/ai-dashboard.component').then(m => m.AiDashboardComponent)
      },
      {
        path: 'lms-author',
        canActivate: [lmsAuthorGuard],
        loadComponent: () => import('./lms-author/lms-author.component').then(m => m.LmsAuthorComponent)
      },
      {
        path: 'lms-learner',
        loadComponent: () => import('./lms-learner/lms-learner.component').then(m => m.LmsLearnerComponent)
      },
      {
        path: 'billing',
        canActivate: [adminGuard],
        loadComponent: () => import('./features/billing-dashboard/billing-dashboard.component').then(m => m.BillingDashboardComponent)
      },
      {
        path: 'settings',
        canActivate: [adminGuard],
        loadComponent: () => import('./features/settings/workspace-settings/workspace-settings').then(m => m.WorkspaceSettings)
      },
      {
        path: 'admin/tenant',
        canActivate: [superAdminGuard],
        loadComponent: () => import('./features/admin/tenant-onboard.component').then(m => m.TenantOnboardComponent)
      },
      { path: '', redirectTo: 'crm', pathMatch: 'full' }
    ]
  },
  { path: '**', redirectTo: 'login' },
];
