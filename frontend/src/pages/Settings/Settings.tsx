import { useState } from 'react';

const tabs = ['General', 'Camera', 'AI', 'Virtual Camera', 'Servo', 'Streaming', 'OBS', 'Notifications'];

export function Settings(): JSX.Element {
  const [activeTab, setActiveTab] = useState('General');

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold text-white">Settings</h2>

      <div className="flex gap-1 rounded-xl border border-dark-border bg-dark-surface p-1">
        {tabs.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-primary-500/20 text-primary-400'
                : 'text-slate-400 hover:bg-dark-card'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-dark-border bg-dark-card p-6">
        <div style={{ display: activeTab === 'General' ? 'block' : 'none' }}>
          <h3 className="mb-4 text-lg font-semibold text-white">General Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Theme</span>
              <select className="rounded-lg border border-dark-border bg-dark-surface px-3 py-1.5 text-sm text-white">
                <option>Dark</option>
              </select>
            </div>
          </div>
        </div>

        <div style={{ display: activeTab === 'AI' ? 'block' : 'none' }}>
          <div className="space-y-4">
            <h3 className="mb-4 text-lg font-semibold text-white">AI Settings</h3>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Detection Model</span>
              <span className="text-sm font-bold text-primary-400">YOLO11</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Tracker</span>
              <span className="text-sm font-bold text-primary-400">ByteTrack</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Motion Style</span>
              <select className="rounded-lg border border-dark-border bg-dark-surface px-3 py-1.5 text-sm text-white">
                <option>Smooth</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Aggressiveness</span>
              <input type="range" min="1" max="10" defaultValue="5" className="w-32 accent-primary-500" />
            </div>
          </div>
        </div>

        {activeTab !== 'General' && activeTab !== 'AI' && (
          <div>
            <h3 className="mb-4 text-lg font-semibold text-white">{activeTab} Settings</h3>
            <p className="text-sm text-slate-400">Configure {activeTab.toLowerCase()} settings here.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Settings;
