import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const adminGuard: CanActivateFn = (route, state) => {
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
      // Decode JWT safely without external libraries for this demo
      const payload = JSON.parse(atob(token.split('.')[1]));
      const roles = Array.isArray(payload.roles) ? payload.roles : (payload.role ? [payload.role] : []);
      if (roles.includes('TENANT_OWNER') || roles.includes('TENANT_ADMIN') || roles.includes('SUPER_ADMIN')) {
        return true;
      } else {
        console.warn(`AdminGuard rejected access: User does not have admin privileges. Found roles: ${JSON.stringify(roles)}`);
      }
    } catch (e) {
      console.error('Error decoding token', e);
    }
  } else {
    console.warn('AdminGuard rejected access: No token found.');
  }
  router.navigate(['/crm']);
  return false;
};
