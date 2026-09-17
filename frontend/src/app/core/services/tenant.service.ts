import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface TenantOnboardRequest {
  name?: string;
  org_name: string;
  slug?: string;
  email?: string;
  admin_email: string;
  password?: string;
  admin_password: string;
  full_name?: string;
  admin_full_name: string;
  invite_code?: string;
}

export interface PublicOnboardRequest {
  name: string;
  slug?: string;
  email: string;
  password: string;
  full_name: string;
  invite_code?: string;
}

export interface TenantOnboardResponse {
  status: string;
  data: {
    organization_id: string;
    org_name: string;
    slug: string;
    admin_email: string;
    user_id: string;
    access_token: string;
    token_type: string;
    expires_in: number;
  };
}
export interface SlugCheckResponse {
  slug: string;
  available: boolean;
}

export interface OrganizationResponse {
  id: string;
  name: string;
  slug: string;
  subscription_status: string;
  created_at?: string;
}

@Injectable({
  providedIn: 'root',
})
export class TenantService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  checkSlugAvailability(slug: string): Observable<SlugCheckResponse> {
    return this.http.get<SlugCheckResponse>(`${this.apiUrl}/tenants/check-slug/${encodeURIComponent(slug)}`);
  }

  // Uses auth endpoint for single user creation
  publicOnboardTenant(payload: PublicOnboardRequest): Observable<TenantOnboardResponse> {
    return this.http.post<TenantOnboardResponse>(`${this.apiUrl}/auth/onboard`, payload);
  }

  getCurrentOrganization(orgId: string, token: string): Observable<OrganizationResponse> {
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'X-Organization-Id': orgId,
    });
    return this.http.get<OrganizationResponse>(`${this.apiUrl}/organizations/me`, { headers });
  }
}
