// Shared TypeScript types mirroring the FastAPI backend.

export type SystemState =
  | 'BOOTING'
  | 'CONNECTING'
  | 'IDLE'
  | 'STREAMING'
  | 'TRACKING'
  | 'MANUAL'
  | 'HOMING'
  | 'EMERGENCY_STOP'
  | 'ERROR';

export type HealthStatus = 'green' | 'yellow' | 'red';

export type DirectorMode =
  | 'broadcast'
  | 'aggressive'
  | 'wide'
  | 'training'
  | 'manual_assist';

export interface ServoStatus {
  state: SystemState;
  pan: number;
  tilt: number;
  is_emergency_stopped: boolean;
}

export interface DirectorStatus {
  state: SystemState;
  mode: DirectorMode;
}
