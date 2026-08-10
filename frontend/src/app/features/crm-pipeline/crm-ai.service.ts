import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CrmAiService {
  private http = inject(HttpClient);
  private apiUrl = '/api/v1/crm/deals';
  private jobsUrl = '/api/v1/ai/jobs';

  scoreDeal(dealId: string): Observable<{ job_id: string }> {
    return this.http.post<{ job_id: string }>(`${this.apiUrl}/${dealId}/ai-score`, {});
  }

  getJobStatus(jobId: string): Observable<{ status: string, result: any }> {
    return this.http.get<{ status: string, result: any }>(`${this.jobsUrl}/${jobId}`);
  }

  draftFollowUp(dealId: string): Observable<{ draft: string }> {
    return this.http.post<{ draft: string }>(`${this.apiUrl}/${dealId}/draft-followup`, {});
  }
}
