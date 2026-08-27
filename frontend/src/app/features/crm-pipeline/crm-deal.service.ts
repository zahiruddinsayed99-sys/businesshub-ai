import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CrmDeal } from './crm-deal.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class CrmDealService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl + '/crm/deals';

  getDeals(): Observable<CrmDeal[]> {
    return this.http.get<CrmDeal[]>(this.apiUrl);
  }

  updateDealStage(dealId: string, stage: string): Observable<CrmDeal> {
    return this.http.patch<CrmDeal>(`${this.apiUrl}/${dealId}/stage`, { stage });
  }

  createDeal(deal: Partial<CrmDeal>): Observable<CrmDeal> {
    return this.http.post<CrmDeal>(this.apiUrl, deal);
  }

  updateDeal(dealId: string, deal: Partial<CrmDeal>): Observable<CrmDeal> {
    return this.http.patch<CrmDeal>(`${this.apiUrl}/${dealId}`, deal);
  }
}
