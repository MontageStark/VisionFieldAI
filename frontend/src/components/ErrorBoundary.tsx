import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="flex h-full items-center justify-center bg-slate-950 p-6">
            <div className="max-w-md rounded-lg border border-rose-500/30 bg-rose-500/10 p-6 text-center">
              <h2 className="text-lg font-semibold text-rose-400">Something went wrong</h2>
              <p className="mt-2 text-sm text-slate-400">{this.state.error?.message}</p>
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="mt-4 rounded-md bg-slate-700 px-4 py-2 text-sm text-white hover:bg-slate-600 transition-colors"
              >
                Try again
              </button>
            </div>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
