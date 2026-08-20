import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './main-layout.component.html',
  styleUrls: ['./main-layout.component.scss']
})
export class MainLayoutComponent {
  private http = inject(HttpClient);
  private router = inject(Router);

  userName = 'User'; // Placeholder, could be fetched from API/token

  logout() {
    this.http.post('/api/v1/auth/logout', {}).subscribe({
      next: () => this.handleLogoutSuccess(),
      error: () => {
        // Even if the server fails, clear local state
        this.handleLogoutSuccess();
      }
    });
  }

  private handleLogoutSuccess() {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('access_token');
      }
    } catch (e) {
      console.error('Error removing token from localStorage', e);
    }
    this.router.navigate(['/login']);
  }
}
