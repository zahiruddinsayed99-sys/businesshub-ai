import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

export const billingInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 402 && error.error?.error_code === 'ERR_BILLING_001') {
        alert('Workspace locked. No AI credits or seats left. Upgrade plan.');
        router.navigate(['/billing']);
      }
      return throwError(() => error);
    })
  );
};
