import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);

  let token = null;
  let orgId = null;
  try {
    if (typeof localStorage !== 'undefined') {
      token = localStorage.getItem('access_token');
      orgId = localStorage.getItem('organization_id');
    }
  } catch (e) {
    console.error('Error accessing localStorage', e);
  }

  // Clone the request to add the authentication header.
  if (token) {
    let headersConfig: { [name: string]: string | string[] } = {
      Authorization: `Bearer ${token}`
    };
    if (orgId) {
      headersConfig['X-Organization-Id'] = orgId;
    }

    req = req.clone({
      setHeaders: headersConfig
    });
  }

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        // Unauthorized error, remove token and redirect to login
        try {
          if (typeof localStorage !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('organization_id');
            localStorage.removeItem('user_id');
          }
        } catch (e) {}

        router.navigate(['/login']);
      }
      return throwError(() => error);
    })
  );
};
