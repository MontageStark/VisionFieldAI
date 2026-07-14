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

export interface HealthCheck {
  status: 'ok';
  timestamp: number;
  version: string;
}

export interface SystemStateResponse {
  state: SystemState;
  state_value: number;
}

export interface SystemStatusResponse {
  state: SystemState;
  valid_transitions: SystemState[];
  history: Array<{
    from: SystemState | null;
    to: SystemState;
    timestamp: number;
    callbacks_executed: boolean;
  }>;
}

export interface StateTransitionResponse {
  state: SystemState;
  previous_state: SystemState | null;
}

export interface CameraAction {
  pan_angle: number;
  tilt_angle: number;
  zoom: number;
  transition_time: number;
}

export interface DirectorDecision {
  mode: DirectorMode;
  target: CameraAction;
  reasoning: string;
  confidence: number;
  timestamp: number;
  tracking_track_id?: number | null;
}

export interface ComponentHealth {
  name: string;
  status: HealthStatus;
  message: string;
  metrics: Record<string, number>;
  timestamp: number;
}

export interface SystemHealth {
  status: HealthStatus;
  components: Record<string, ComponentHealth>;
  timestamp: number;
  uptime: number;
}

export interface ServoStatus {
  state: SystemState;
  pan: number;
  tilt: number;
  is_emergency_stopped: boolean;
}

export interface ServoCommandRequest {
  pan: number;
  tilt: number;
}

export interface StreamStatus {
  active: boolean;
  fps: number;
  bitrate_kbps: number;
  url?: string;
}

export interface DirectorStatus {
  state: SystemState;
  mode: DirectorMode;
  last_decision?: DirectorDecision;
}

export interface WebSocketMessage {
  type: 'pong' | 'subscribed' | 'error' | string;
  topic?: string;
  message?: string;
  timestamp?: number;
}
