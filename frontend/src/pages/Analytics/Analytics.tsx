import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const metrics = [
  { name: 'FPS', value: '60', color: 'text-accent-success' },
  { name: 'GPU', value: '45%', color: 'text-primary-400' },
  { name: 'CPU', value: '32%', color: 'text-primary-400' },
  { name: 'Memory', value: '2.1GB', color: 'text-accent-warning' },
  { name: 'Latency', value: '12ms', color: 'text-accent-success' },
];

const chartData = Array.from({ length: 20 }, (_, i) => ({
  time: i,
  fps: 55 + Math.random() * 10,
  gpu: 30 + Math.random() * 30,
  cpu: 20 + Math.random() * 20,
}));

export function Analytics(): JSX.Element {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Analytics</h2>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {metrics.map((m) => (
          <div key={m.name} className="rounded-xl border border-dark-border bg-dark-card p-4">
            <p className="text-xs text-slate-400">{m.name}</p>
            <p className={`text-2xl font-bold ${m.color}`}>{m.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-xl border border-dark-border bg-dark-card p-4">
          <h3 className="mb-4 text-sm font-semibold text-white">FPS History</h3>
          <div data-testid="chart-container" className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A3344" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={10} />
                <YAxis stroke="#64748B" fontSize={10} />
                <Tooltip contentStyle={{ background: '#1C2330', border: '1px solid #2A3344' }} />
                <Line type="monotone" dataKey="fps" stroke="#10B981" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-dark-border bg-dark-card p-4">
          <h3 className="mb-4 text-sm font-semibold text-white">GPU / CPU Usage</h3>
          <div data-testid="chart-container" className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A3344" />
                <XAxis dataKey="time" stroke="#64748B" fontSize={10} />
                <YAxis stroke="#64748B" fontSize={10} />
                <Tooltip contentStyle={{ background: '#1C2330', border: '1px solid #2A3344' }} />
                <Area type="monotone" dataKey="gpu" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.1} />
                <Area type="monotone" dataKey="cpu" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-dark-border bg-dark-card p-4">
        <h3 className="mb-2 text-sm font-semibold text-white">Detection Count</h3>
        <p className="text-3xl font-bold text-primary-400">1,247</p>
        <p className="text-xs text-slate-400">Total players tracked this session</p>
      </div>
    </div>
  );
}

export default Analytics;
