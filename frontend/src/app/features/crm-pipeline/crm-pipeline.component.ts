import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CdkDragDrop, DragDropModule, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { CrmDealService } from './crm-deal.service';
import { CrmAiService } from './crm-ai.service';
import { CrmDeal } from './crm-deal.model';
import { Subject, timer } from 'rxjs';
import { switchMap, takeWhile, debounceTime } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-crm-pipeline',
  standalone: true,
  imports: [CommonModule, DragDropModule, FormsModule],
  templateUrl: './crm-pipeline.component.html',
  styleUrls: ['./crm-pipeline.component.scss']
})
export class CrmPipelineComponent implements OnInit {
  private stageUpdateSubject = new Subject<{ deal: CrmDeal, newStage: string, oldStage: string }>();
  private crmService = inject(CrmDealService);
  private crmAiService = inject(CrmAiService);
  private http = inject(HttpClient);

  deals = signal<CrmDeal[]>([]);
  filterMode = signal<'ALL' | 'MINE'>('ALL');
  currentUserId = signal<string | null>(null);
  errorToast = signal<string | null>(null);

  scoringJobs = signal<Record<string, string>>({});

  draftModalVisible = signal<boolean>(false);
  draftContent = signal<string>('');
  draftLoading = signal<boolean>(false);

  createModalVisible = signal<boolean>(false);
  editModalVisible = signal<boolean>(false);

  newDealData = signal<Partial<CrmDeal>>({
    title: '',
    value_amount: 0,
    currency: 'INR',
    stage: 'LEAD',
    expected_close_date: ''
  });

  editingDealData = signal<Partial<CrmDeal>>({});

  openCreateModal() {
    this.newDealData.set({
      title: '',
      value_amount: 0,
      currency: 'INR',
      stage: 'LEAD',
      expected_close_date: ''
    });
    this.createModalVisible.set(true);
  }

  closeCreateModal() {
    this.createModalVisible.set(false);
  }

  submitCreateDeal() {
    const data = this.newDealData();
    if (!data.title || !data.value_amount) {
      this.showErrorToast("Title and Value are required.");
      return;
    }

    const payload: any = {
       title: data.title,
       value_amount: Number(data.value_amount),
       currency: data.currency || 'INR',
       stage: data.stage
    };

    if (data.expected_close_date && data.expected_close_date.trim() !== '') {
       payload.expected_close_date = data.expected_close_date;
    } else {
       payload.expected_close_date = null;
    }

    this.crmService.createDeal(payload).subscribe({
      next: (deal) => {
        this.loadDeals();
        this.closeCreateModal();
      },
      error: (err) => {
        console.error(err);
        this.showErrorToast("Failed to create deal.");
      }
    });
  }

  openEditModal(deal: CrmDeal) {
    this.editingDealData.set({ ...deal });
    this.editModalVisible.set(true);
  }

  closeEditModal() {
    this.editModalVisible.set(false);
  }

  submitEditDeal() {
    const data = this.editingDealData();
    if (!data.id) return;

    const payload: any = {
      title: data.title,
      value_amount: Number(data.value_amount),
      currency: data.currency || 'INR',
      stage: data.stage
    };

    if (data.expected_close_date && typeof data.expected_close_date === 'string' && data.expected_close_date.trim() !== '') {
       payload.expected_close_date = data.expected_close_date;
    } else if (!data.expected_close_date || (typeof data.expected_close_date === 'string' && data.expected_close_date.trim() === '')) {
       payload.expected_close_date = null;
    }

    this.crmService.updateDeal(data.id, payload).subscribe({
      next: (deal) => {
        this.loadDeals();
        this.closeEditModal();
      },
      error: (err) => {
        console.error(err);
        this.showErrorToast("Failed to update deal.");
      }
    });
  }



  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(value);
  }

  columns = ['LEAD', 'QUALIFIED', 'PROPOSAL', 'WON', 'LOST'];

  filteredDeals = computed(() => {
    const all = this.deals();
    const mode = this.filterMode();
    const userId = this.currentUserId();

    if (mode === 'MINE' && userId) {
      return all.filter(d => d.owner_user_id === userId);
    }
    return all;
  });

  ngOnInit() {
    this.stageUpdateSubject.pipe(
      debounceTime(300)
    ).subscribe(({ deal, newStage, oldStage }) => {
      this.crmService.updateDealStage(deal.id, newStage).subscribe({
        error: (err) => {
          console.error(err);
          // Rollback on failure (Optimistic UI fallback)
          this.deals.update(deals => {
            return deals.map(d =>
              d.id === deal.id ? { ...d, stage: oldStage } : d
            );
          });
          this.showErrorToast("Failed to update deal stage. Rolled back.");
        }
      });
    });

    const me = localStorage.getItem('user_id');
    if (me) {
      this.currentUserId.set(me);
      this.loadDeals();
    } else {
      this.http.get<any>(`${environment.apiUrl}/auth/me`).subscribe({
        next: (data) => {
          if (data.user_id) {
            this.currentUserId.set(data.user_id);
            try {
              if (typeof localStorage !== 'undefined') {
                localStorage.setItem('user_id', data.user_id);
              }
            } catch (e) {}
          }
          this.loadDeals();
        },
        error: (e) => {
          console.error(e);
          this.loadDeals(); // Try anyway, let it fail cleanly
        }
      });
    }
  }

  loadDeals() {
    this.crmService.getDeals().subscribe({
      next: (data) => this.deals.set(data),
      error: (err) => console.error('Failed to load deals', err)
    });
  }

  getDealsByStage(stage: string): CrmDeal[] {
    return this.filteredDeals().filter(d => d.stage === stage);
  }

  setFilter(mode: 'ALL' | 'MINE') {
    this.filterMode.set(mode);
  }

  drop(event: CdkDragDrop<CrmDeal[]>, newStage: string) {
    if (event.previousContainer === event.container) {
      const list = event.container.data;
      moveItemInArray(list, event.previousIndex, event.currentIndex);
    } else {
      const deal = event.previousContainer.data[event.previousIndex];
      const oldStage = deal.stage;

      // Optimistic update: instantly move the deal locally
      this.deals.update(deals => {
        return deals.map(d =>
          d.id === deal.id ? { ...d, stage: newStage } : d
        );
      });

      // API Call execution
      this.stageUpdateSubject.next({ deal, newStage, oldStage });
    }
  }

  showErrorToast(msg: string) {
    this.errorToast.set(msg);
    setTimeout(() => this.errorToast.set(null), 3000);
  }

  scoreDeal(deal: CrmDeal) {
    this.crmAiService.scoreDeal(deal.id).subscribe({
      next: (response) => {
        this.scoringJobs.update(jobs => ({ ...jobs, [deal.id]: response.job_id }));
        this.pollJobStatus(response.job_id, deal.id);
      },
      error: (err) => {
        console.error('Failed to trigger score', err);
        this.showErrorToast("Failed to initiate AI scoring.");
      }
    });
  }

  private pollJobStatus(jobId: string, dealId: string) {
    timer(0, 2000).pipe(
      switchMap(() => this.crmAiService.getJobStatus(jobId)),
      takeWhile(res => res.status === 'PENDING' || res.status === 'STARTED', true)
    ).subscribe({
      next: (res) => {
        if (res.status === 'SUCCESS' && res.result?.status === 'completed') {
          this.loadDeals();
          this.scoringJobs.update(jobs => {
            const newJobs = { ...jobs };
            delete newJobs[dealId];
            return newJobs;
          });
        } else if (res.status === 'FAILURE') {
          this.showErrorToast("AI Scoring job failed.");
          this.scoringJobs.update(jobs => {
            const newJobs = { ...jobs };
            delete newJobs[dealId];
            return newJobs;
          });
        }
      },
      error: (err) => {
        console.error('Polling failed', err);
        this.scoringJobs.update(jobs => {
          const newJobs = { ...jobs };
          delete newJobs[dealId];
          return newJobs;
        });
      }
    });
  }

  draftFollowUp(deal: CrmDeal) {
    this.draftModalVisible.set(true);
    this.draftLoading.set(true);
    this.draftContent.set('');

    this.crmAiService.draftFollowUp(deal.id).subscribe({
      next: (response) => {
        this.draftContent.set(response.draft);
        this.draftLoading.set(false);
      },
      error: (err) => {
        console.error('Failed to draft followup', err);
        this.draftModalVisible.set(false);
        this.showErrorToast("Failed to draft AI follow-up.");
        this.draftLoading.set(false);
      }
    });
  }

  closeDraftModal() {
    this.draftModalVisible.set(false);
  }

  copyToClipboard() {
    navigator.clipboard.writeText(this.draftContent()).then(() => {
      // Could show a "copied" toast
    });
  }
}
