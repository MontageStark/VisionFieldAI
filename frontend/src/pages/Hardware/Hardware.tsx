import { useState, useEffect } from 'react'
import { useAppStore } from '@/stores/appStore'
import { servoApi } from '@/services/api'

interface ServoStatus {
  connected: boolean
  pan_angle: number
  tilt_angle: number
}

interface PTZStatus {
  available: boolean
  host: string
  connected: boolean
}

export default function Hardware() {
  const { outputMode } = useAppStore()
  const [servo, setServo] = useState<ServoStatus>({
    connected: false,
    pan_angle: 90,
    tilt_angle: 90,
  })
  const [ptz] = useState<PTZStatus>({
    available: false,
    host: '192.168.1.100',
    connected: false,
  })

  const isServoActive = outputMode === 'servo' || outputMode === 'hybrid'
  const isPTZActive = outputMode === 'ptz'

  useEffect(() => {
    if (!isServoActive) return
    const interval = setInterval(async () => {
      try {
        const response = await servoApi.status()
        setServo({
          connected: true,
          pan_angle: response.pan ?? 90,
          tilt_angle: response.tilt ?? 90,
        })
      } catch {
        setServo(prev => ({ ...prev, connected: false }))
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [isServoActive])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-white">Hardware</h1>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className={`rounded-xl p-6 border ${
          isServoActive
            ? 'bg-dark-card border-primary-500/30'
            : 'bg-dark-card/50 border-dark-border opacity-60'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Servo Camera</h3>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              isServoActive
                ? 'bg-accent-success/20 text-accent-success'
                : 'bg-dark-border text-slate-400'
            }`}>
              {isServoActive ? 'Active' : 'Inactive'}
            </span>
          </div>

          {isServoActive ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-dark-surface rounded-lg p-3">
                  <div className="text-slate-300 text-xs mb-1">Pan Angle</div>
                  <div className="text-2xl font-mono text-white">{servo.pan_angle.toFixed(1)}°</div>
                </div>
                <div className="bg-dark-surface rounded-lg p-3">
                  <div className="text-slate-300 text-xs mb-1">Tilt Angle</div>
                  <div className="text-2xl font-mono text-white">{servo.tilt_angle.toFixed(1)}°</div>
                </div>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className={`w-2 h-2 rounded-full ${servo.connected ? 'bg-accent-success' : 'bg-accent-error'}`} />
                <span className="text-slate-300">
                  {servo.connected ? 'Connected to ESP32' : 'Disconnected'}
                </span>
              </div>
            </div>
          ) : (
            <div className="text-slate-400 text-sm">
              Enable Servo mode in Settings to control ESP32 servo motors.
            </div>
          )}
        </div>

        <div className={`rounded-xl p-6 border ${
          isPTZActive
            ? 'bg-dark-card border-primary-500/30'
            : 'bg-dark-card/50 border-dark-border opacity-60'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">PTZ Camera</h3>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              isPTZActive
                ? 'bg-accent-success/20 text-accent-success'
                : 'bg-dark-border text-slate-400'
            }`}>
              {isPTZActive ? 'Active' : 'Inactive'}
            </span>
          </div>

          <div className="space-y-4">
            <div className="bg-dark-surface rounded-lg p-3">
              <div className="text-slate-300 text-xs mb-1">Host</div>
              <div className="text-white font-mono">{ptz.host}</div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${ptz.connected ? 'bg-accent-success' : 'bg-slate-500'}`} />
              <span className="text-slate-300">
                {ptz.connected ? 'Connected' : 'Not connected'}
              </span>
            </div>
            <div className="text-slate-400 text-sm">
              PTZ support coming soon. Enable PTZ mode in Settings to use ONVIF cameras.
            </div>
          </div>
        </div>
      </div>

      <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
        <h3 className="text-sm text-slate-300 uppercase tracking-wider mb-3">Current Output</h3>
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${
            outputMode === 'virtual' ? 'bg-primary-500' :
            outputMode === 'servo' ? 'bg-accent-success' :
            outputMode === 'hybrid' ? 'bg-accent-warning' :
            'bg-accent-info'
          }`} />
          <span className="text-white font-medium capitalize">{outputMode} Camera</span>
          <span className="text-slate-400 text-sm">
            {outputMode === 'virtual' && 'Software-only rendering — no hardware needed'}
            {outputMode === 'servo' && 'ESP32 servo motor control active'}
            {outputMode === 'hybrid' && 'Servo + virtual camera fine-tuning'}
            {outputMode === 'ptz' && 'ONVIF PTZ camera control'}
          </span>
        </div>
      </div>
    </div>
  )
}
