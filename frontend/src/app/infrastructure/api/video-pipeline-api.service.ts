import { Injectable } from '@angular/core';
import { Observable, from } from 'rxjs';
import { VideoJob } from '../../domain/models/video-job.model';

@Injectable({
  providedIn: 'root'
})
export class VideoPipelineApiService {
  private readonly baseUrl = '/api/v1';

  submitJob(filename: string, estimatedFrames: number, storageUri: string): Observable<VideoJob> {
    const promise = fetch(`${this.baseUrl}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename,
        estimated_frames: estimatedFrames,
        storage_uri: storageUri
      })
    })
      .then(res => res.json())
      .then(data => this.mapResponse(data));

    return from(promise);
  }

  getJobStatus(jobId: string): Observable<VideoJob> {
    const promise = fetch(`${this.baseUrl}/jobs/${jobId}`)
      .then(res => res.json())
      .then(data => this.mapResponse(data));

    return from(promise);
  }

  private mapResponse(data: any): VideoJob {
    return {
      jobId: data.job_id,
      filename: data.filename,
      totalFrames: data.total_frames,
      processedFrames: data.processed_frames,
      status: data.status,
      progressPercentage: data.progress_percentage,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
      detections: (data.detections || []).map((d: any) => ({
        frameNumber: d.frame_number,
        timestampSec: d.timestamp_sec,
        inferenceLatencyMs: d.inference_latency_ms,
        boxes: (d.boxes || []).map((b: any) => ({
          xMin: b.x_min,
          yMin: b.y_min,
          xMax: b.x_max,
          yMax: b.y_max,
          confidence: b.confidence,
          className: b.class_name
        }))
      })),
      userMessage: data.user_message
    };
  }
}
