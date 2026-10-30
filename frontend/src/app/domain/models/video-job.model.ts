export type JobStatus = 'PENDING' | 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface BoundingBox {
  xMin: number;
  yMin: number;
  xMax: number;
  yMax: number;
  confidence: number;
  className: string;
}

export interface Detection {
  frameNumber: number;
  timestampSec: number;
  boxes: BoundingBox[];
  inferenceLatencyMs: number;
}

export interface VideoJob {
  jobId: string;
  filename: string;
  totalFrames: number;
  processedFrames: number;
  status: JobStatus;
  progressPercentage: number;
  createdAt: string;
  updatedAt: string;
  detections: Detection[];
  userMessage: string;
}
