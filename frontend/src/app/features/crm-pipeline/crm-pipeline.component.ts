import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CdkDragDrop, DragDropModule, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { CrmDealService } from './crm-deal.service';
import { CrmDeal } from './crm-deal.model';
import { catchError } from 'rxjs/operators';
import { of, Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';

// Mock auth service for getting current user
@Component({
  selector: 'app-crm-pipeline',
  standalone: true,
  imports: [CommonModule, DragDropModule],
  templateUrl: './crm-pipeline.component.html',
  styleUrls: ['./crm-pipeline.component.scss']
})
export class CrmPipelineComponent implements OnInit {
  private stageUpdateSubject = new Subject<{deal: CrmDeal, newStage: string, oldStage: string}>();
  private crmService = inject(CrmDealService);

  // Use Signals for state management
  deals = signal<CrmDeal[]>([]);
  filterMode = signal<'ALL' | 'MINE'>('ALL');
  currentUserId = signal<string | null>(null); // Ideally from an auth service
  errorToast = signal<string | null>(null);

  columns = ['LEAD', 'QUALIFIED', 'PROPOSAL', 'WON', 'LOST'];

  // Computed signal to filter deals based on toggle
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
      debounceTime(500)
    ).subscribe(({deal, newStage, oldStage}) => {
      this.crmService.updateDealStage(deal.id, newStage).subscribe({
        error: (err) => {
          console.error(err);
          // Rollback on failure
          this.deals.update(deals => {
            return deals.map(d =>
              d.id === deal.id ? { ...d, stage: oldStage } : d
            );
          });
          this.showErrorToast("Failed to update deal stage. Rolled back.");
        }
      });
    });
    // In a real app, we'd get this from a real Auth service
    const me = localStorage.getItem('user_id'); // Just an example
    if (me) {
      this.currentUserId.set(me);
    } else {
      // Fetch /api/v1/auth/me here to get user ID if needed,
      // but for testing we can assume it works if we have it in memory somewhere
      fetch('/api/v1/auth/me').then(r => r.json()).then(data => {
         if (data.user_id) this.currentUserId.set(data.user_id);
      }).catch(e => console.error(e));
    }
    this.loadDeals();
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
      // Reordering in same column (optional)
      const list = event.container.data;
      moveItemInArray(list, event.previousIndex, event.currentIndex);
    } else {
      const deal = event.previousContainer.data[event.previousIndex];
      const oldStage = deal.stage;

      // Optimistic update
      this.deals.update(deals => {
        return deals.map(d =>
          d.id === deal.id ? { ...d, stage: newStage } : d
        );
      });

      // API Call with debounce/immediate
      this.stageUpdateSubject.next({deal, newStage, oldStage});
    }
  }

  showErrorToast(msg: string) {
    this.errorToast.set(msg);
    setTimeout(() => this.errorToast.set(null), 3000);
  }
}
