import { Component, inject, OnInit, ChangeDetectionStrategy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './main-layout.component.html',
  styleUrls: ['./main-layout.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MainLayoutComponent implements OnInit {
  private http = inject(HttpClient);
  private router = inject(Router);

  userName = signal<string>('User');
  userRole = signal<string>('');

  ngOnInit() {
    this.http.get<any>(`${environment.apiUrl}/auth/me`).subscribe({
      next: (res) => {
        this.userName.set(res.email); // or full_name if available
        this.userRole.set(res.role);
      },
      error: () => {
        // Handle error by parsing JWT as fallback
        let token = null;
        try {
          if (typeof localStorage !== 'undefined') {
            token = localStorage.getItem('access_token');
          }
        } catch (e) { }

        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            this.userRole.set(payload.role);
            this.userName.set(payload.email || 'User');
          } catch (e) { }
        }
      }
    });
  }

  logout() {
    this.http.post(`${environment.apiUrl}/auth/logout`, {}).subscribe({
      next: () => this.handleLogoutSuccess(),
      error: () => this.handleLogoutSuccess()
    });
  }

  private handleLogoutSuccess() {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('organization_id');
        localStorage.removeItem('user_id');
      }
    } catch (e) { }
    this.router.navigate(['/login']);
  }
}
