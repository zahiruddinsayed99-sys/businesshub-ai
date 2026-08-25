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
      const roles = Array.isArray(payload.roles) ? payload.roles : (payload.role ? [payload.role] : []);
      if (roles.includes('SUPER_ADMIN')) {
        return true;
      } else {
        console.warn(`SuperAdminGuard rejected access: User does not have SUPER_ADMIN privileges. Found roles: ${JSON.stringify(roles)}`);
      }
    } catch (e) {
      console.error('Error decoding token', e);
    }
  } else {
    console.warn('SuperAdminGuard rejected access: No token found.');
  }
  router.navigate(['/crm']);
  return false;
};
