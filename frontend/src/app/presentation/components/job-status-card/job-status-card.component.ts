import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VideoJob } from '../../domain/models/video-job.model';

@Component({
  selector: 'app-job-status-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="job-card" *ngIf="job">
      <div class="card-header">
        <div>
          <h4>{{ job.filename }}</h4>
          <span class="job-id">UUID: <code>{{ job.jobId }}</code></span>
        </div>
        <div class="badge" [ngClass]="job.status.toLowerCase()">
          {{ job.status }}
        </div>
      </div>

      <div class="progress-bar-container">
        <div class="progress-bar" [style.width.%]="job.progressPercentage"></div>
      </div>

      <div class="meta-row">
        <span>Progresso: <strong>{{ job.processedFrames }} / {{ job.totalFrames }} frames</strong> ({{ job.progressPercentage }}%)</span>
        <span>Última atualização: {{ job.updatedAt | date:'HH:mm:ss' }}</span>
      </div>

      <div class="user-msg">
        💡 {{ job.userMessage }}
      </div>

      <div class="detections-preview" *ngIf="job.detections.length > 0">
        <h5>Amostra de Detecções YOLOv8 Recentes ({{ job.detections.length }} frames):</h5>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Frame</th>
                <th>Tempo</th>
                <th>Objetos Detectados</th>
                <th>Latência</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let det of job.detections.slice(0, 5)">
                <td>#{{ det.frameNumber }}</td>
                <td>{{ det.timestampSec }}s</td>
                <td>
                  <span class="box-tag" *ngFor="let b of det.boxes">
                    {{ b.className }} ({{ (b.confidence * 100) | number:'1.0-0' }}%)
                  </span>
                </td>
                <td>{{ det.inferenceLatencyMs }}ms</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .job-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      margin-top: 20px;
    }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .job-id { font-size: 0.8rem; color: var(--text-muted); }
    .badge {
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
    }
    .badge.completed { background: rgba(16, 185, 129, 0.2); color: var(--status-completed); }
    .badge.processing { background: rgba(59, 130, 246, 0.2); color: var(--status-processing); }
    .badge.queued { background: rgba(234, 179, 8, 0.2); color: var(--status-queued); }
    .progress-bar-container {
      height: 8px;
      background: var(--bg-card);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 12px;
    }
    .progress-bar {
      height: 100%;
      background: linear-gradient(90deg, var(--accent-orange), var(--accent-amber));
      transition: width 0.3s;
    }
    .meta-row { display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 12px; }
    .user-msg {
      background: var(--bg-card);
      border-left: 3px solid var(--accent-amber);
      padding: 10px 14px;
      border-radius: 4px;
      font-size: 0.85rem;
      margin-bottom: 16px;
    }
    .detections-preview h5 { font-size: 0.9rem; margin-bottom: 10px; color: var(--text-muted); }
    .table-scroll { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border-color); }
    th { color: var(--text-muted); font-weight: 500; }
    .box-tag {
      display: inline-block;
      background: rgba(139, 92, 246, 0.2);
      color: var(--accent-purple);
      border: 1px solid var(--accent-purple);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.75rem;
      margin-right: 4px;
    }
  `]
})
export class JobStatusCardComponent {
  @Input() job: VideoJob | null = null;
}
