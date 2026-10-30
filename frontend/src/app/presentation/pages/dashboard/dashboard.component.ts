import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BatchUploadComponent } from '../../components/batch-upload/batch-upload.component';
import { JobStatusCardComponent } from '../../components/job-status-card/job-status-card.component';
import { VideoPipelineApiService } from '../../../infrastructure/api/video-pipeline-api.service';
import { VideoJob } from '../../../domain/models/video-job.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BatchUploadComponent, JobStatusCardComponent],
  template: `
    <div class="dashboard-shell">
      <header class="navbar">
        <div class="brand">
          <span class="logo">🎥</span>
          <h2>Distributed Video Inference Pipeline</h2>
        </div>
        <div class="metrics-pill">
          <span>RabbitMQ + YOLOv8 Active</span>
        </div>
      </header>

      <main class="content">
        <app-batch-upload (jobSubmitted)="handleJobSubmission($event)"></app-batch-upload>
        <app-job-status-card [job]="activeJob"></app-job-status-card>
      </main>
    </div>
  `,
  styles: [`
    .dashboard-shell { max-width: 1000px; margin: 0 auto; padding: 32px 20px; }
    .navbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 20px;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .logo { font-size: 1.8rem; }
    h2 { font-size: 1.4rem; font-weight: 700; }
    .metrics-pill {
      font-size: 0.85rem;
      background: rgba(249, 115, 22, 0.1);
      color: var(--accent-orange);
      padding: 6px 14px;
      border-radius: 20px;
      font-weight: 500;
    }
  `]
})
export class DashboardComponent {
  activeJob: VideoJob | null = null;

  constructor(private pipelineApi: VideoPipelineApiService) {}

  handleJobSubmission(event: { filename: string; estimatedFrames: number; storageUri: string }) {
    this.pipelineApi.submitJob(event.filename, event.estimatedFrames, event.storageUri).subscribe({
      next: (job) => {
        this.activeJob = job;
      },
      error: (err) => console.error('Erro ao submeter job', err)
    });
  }
}
