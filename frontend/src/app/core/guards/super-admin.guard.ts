import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const superAdminGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  let token = null;
  try {
    if (typeof localStorage !== 'undefined') {
      token = localStorage.getItem('access_token');
    }
  } catch (e) {
    console.error('Error accessing localStorage', e);
  }

  if (token) {
    try {
      // Decode JWT safely
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.role === 'SUPER_ADMIN') {
        return true;
      }
    } catch (e) {
      console.error('Error decoding token', e);
    }
  }
  return router.createUrlTree(['/crm']); // or login
};
