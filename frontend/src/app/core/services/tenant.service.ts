import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface TenantOnboardRequest {
  org_name: string;
  slug?: string;
  admin_email: string;
  admin_password: string;
  admin_full_name: string;
}

export interface TenantOnboardResponse {
  organization_id: string;
  org_name: string;
  slug: string;
  admin_user_id: string;
  admin_email: string;
  access_token: string;
  token_type: string;
  expires_in: number;
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
  private apiUrl = '/api/v1';

  constructor(private http: HttpClient) {}

  checkSlugAvailability(slug: string): Observable<SlugCheckResponse> {
    return this.http.get<SlugCheckResponse>(`${this.apiUrl}/tenants/check-slug/${encodeURIComponent(slug)}`);
  }

  onboardTenant(payload: TenantOnboardRequest): Observable<TenantOnboardResponse> {
    return this.http.post<TenantOnboardResponse>(`${this.apiUrl}/tenants/onboard`, payload);
  }

  getCurrentOrganization(orgId: string, token: string): Observable<OrganizationResponse> {
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'X-Organization-Id': orgId,
    });
    return this.http.get<OrganizationResponse>(`${this.apiUrl}/organizations/me`, { headers });
  }
}
