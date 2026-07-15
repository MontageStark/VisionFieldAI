import { useEffect } from 'react';
import { useAppStore } from '@/stores/appStore';

export default function Settings(): JSX.Element {
  const { outputMode, setOutputMode, fetchOutputState } = useAppStore();

  useEffect(() => {
    fetchOutputState();
  }, [fetchOutputState]);

  return (
    <div className="space-y-6">
      <section className="bg-dark-800 rounded-xl p-6 border border-dark-600">
        <h2 className="text-lg font-semibold text-white mb-4">Camera Output</h2>
        <p className="text-dark-400 text-sm mb-4">
          Choose how the AI Director's decisions are rendered. Virtual Camera is the default — no hardware required.
        </p>
        <div className="space-y-3">
          {[
            { value: 'virtual', label: 'Virtual Camera', desc: 'Crop/pan/zoom in software — no hardware needed' },
            { value: 'servo', label: 'Servo Camera', desc: 'Control servo motors via ESP32' },
            { value: 'hybrid', label: 'Hybrid', desc: 'Servo + virtual camera fine-tuning' },
            { value: 'ptz', label: 'PTZ Camera', desc: 'ONVIF-based professional PTZ camera' },
          ].map(opt => (
            <label
              key={opt.value}
              className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                outputMode === opt.value
                  ? 'bg-primary-500/10 border border-primary-500/30'
                  : 'bg-dark-700 border border-dark-600 hover:border-dark-500'
              }`}
            >
              <input
                type="radio"
                name="outputMode"
                value={opt.value}
                checked={outputMode === opt.value}
                onChange={() => setOutputMode(opt.value as any)}
                className="mt-1 accent-primary-500"
              />
              <div>
                <div className="text-white font-medium">{opt.label}</div>
                <div className="text-dark-400 text-sm">{opt.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </section>
    </div>
  );
}
