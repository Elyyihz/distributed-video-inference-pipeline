import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-batch-upload',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="submission-card">
      <h3>Novo Job de Processamento em Lote</h3>
      <p class="desc">Envie um fluxo de vídeo para decomposição distribuída e inferência de visão paralela.</p>

      <div class="form-grid">
        <div class="form-group">
          <label>Identificador do Arquivo / Câmera:</label>
          <input type="text" [(ngModel)]="filename" placeholder="ex: camera_norte_rodovia_04.mp4" />
        </div>
        <div class="form-group">
          <label>Estimativa de Frames Totais:</label>
          <input type="number" [(ngModel)]="estimatedFrames" placeholder="ex: 300" />
        </div>
      </div>

      <div class="actions">
        <button class="btn-submit" (click)="onSubmit()">Enfileirar no RabbitMQ</button>
      </div>
    </div>
  `,
  styles: [`
    .submission-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }
    h3 { font-size: 1.2rem; font-weight: 600; margin-bottom: 6px; }
    .desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 20px; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
    .form-group label { display: block; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px; }
    .form-group input {
      width: 100%;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.9rem;
    }
    .actions { text-align: right; }
    .btn-submit {
      background: linear-gradient(135deg, var(--accent-orange), var(--accent-amber));
      border: none;
      color: #fff;
      font-weight: 600;
      padding: 10px 22px;
      border-radius: 6px;
      cursor: pointer;
    }
  `]
})
export class BatchUploadComponent {
  filename = 'cctv_highway_sample.mp4';
  estimatedFrames = 300;

  @Output() jobSubmitted = new EventEmitter<{ filename: string; estimatedFrames: number; storageUri: string }>();

  onSubmit() {
    this.jobSubmitted.emit({
      filename: this.filename,
      estimatedFrames: this.estimatedFrames,
      storageUri: `/storage/videos/${this.filename}`
    });
  }
}
