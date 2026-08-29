import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const lmsAuthorGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  let token = null;
  try {
    if (typeof localStorage !== 'undefined') {
      token = localStorage.getItem('access_token');
    }
  } catch (e) {}

  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const roles = Array.isArray(payload.roles) ? payload.roles : [payload.role];
      const hasAccess = roles.some((r: any) => ['TENANT_OWNER', 'TENANT_ADMIN', 'SUPER_ADMIN', 'LMS_MANAGER'].includes(r));
      if (hasAccess) {
        return true;
      }
    } catch (e) {}
  }
  return router.createUrlTree(['/crm']);
};
