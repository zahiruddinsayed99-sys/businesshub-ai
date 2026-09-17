import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class CrmAiService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl + '/crm/deals';
  private jobsUrl = environment.apiUrl + '/ai/jobs';

  scoreDeal(dealId: string): Observable<{ deal_id: string }> {
    return this.http.post<{ deal_id: string }>(`${this.apiUrl}/${dealId}/ai-score`, {});
  }

  getJobStatus(jobId: string): Observable<{ status: string, result: any }> {
    return this.http.get<{ status: string, result: any }>(`${this.jobsUrl}/${jobId}`);
  }

  draftFollowUp(dealId: string): Observable<{ draft: string }> {
    return this.http.post<{ draft: string }>(`${this.apiUrl}/${dealId}/draft-followup`, {});
  }
}
