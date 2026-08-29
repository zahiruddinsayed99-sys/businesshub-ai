import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);

  // Try to get token from localStorage safely
  let token = null;
  try {
    if (typeof localStorage !== 'undefined') {
      token = localStorage.getItem('access_token');
    }
  } catch (e) {
    console.error('Error accessing localStorage', e);
  }

  if (token) {
    return true;
  }

  // Not logged in, redirect to login page
  return router.createUrlTree(['/login']);
};
