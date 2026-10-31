import { useEffect, useState } from 'react';
import { apiClient } from './api/client';
import { 
  Server, 
  Database, 
  ShieldCheck, 
  Cpu, 
  RefreshCw,
  GitBranch,
  Terminal
} from 'lucide-react';

interface HealthData {
  status: string;
  service: string;
  version: string;
  database: {
    status: string;
    database_engine: string;
    version: string;
    current_database: string;
  };
}

export function App() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get<HealthData>('/health');
      setHealth(res.data);
      setLastChecked(new Date());
    } catch (err: any) {
      setError(err?.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-indigo-600 p-2 rounded-lg shadow-lg shadow-indigo-500/30 text-white">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-wide">
              Brightloop Nexus
            </h1>
            <p className="text-xs text-indigo-400 font-medium">
              Member 1: Subscription & Intelligence Engine
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
            Phase 1: Active
          </span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition border border-slate-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Check Connectivity</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 space-y-8">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900 to-slate-900 p-8 rounded-2xl border border-indigo-900/40 shadow-2xl">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-indigo-400 bg-indigo-950/80 px-3 py-1 rounded-md border border-indigo-800/50">
              <GitBranch className="w-3.5 h-3.5" />
              <span>Phase 1 Initialized — Project Setup & MySQL Connection</span>
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight">
              Enterprise Subscription & Revenue Architecture
            </h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              Brightloop Nexus is built with a decoupled microservice-ready architecture. Member 1 provides complete customer lifecycle management, subscription state machines, renewal automation, and predictive Churn Radar intelligence.
            </p>
          </div>
        </div>

        {/* Live Diagnostics Card Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Backend API Service */}
          <div className="bg-slate-950/60 p-6 rounded-xl border border-slate-800 space-y-4 hover:border-slate-700 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Backend API</span>
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                <Server className="w-5 h-5" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-white">FastAPI</span>
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-900/60 text-indigo-300 font-mono">v1.0.0</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">Python 3.12 • Pydantic v2 • SQLAlchemy 2.0</p>
            </div>
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-500">API Gateway:</span>
              <span className="text-emerald-400 font-mono font-medium">http://localhost:8000/api/v1</span>
            </div>
          </div>

          {/* Card 2: Relational Database */}
          <div className="bg-slate-950/60 p-6 rounded-xl border border-slate-800 space-y-4 hover:border-slate-700 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Database Engine</span>
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <Database className="w-5 h-5" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-white">MySQL 8.0+</span>
                {health?.database.status === 'connected' ? (
                  <span className="text-xs px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300 font-mono">Connected</span>
                ) : (
                  <span className="text-xs px-2 py-0.5 rounded bg-rose-900/60 text-rose-300 font-mono">Connecting...</span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Database: <span className="font-mono text-slate-200">{health?.database.current_database || 'brightloop_nexus'}</span>
              </p>
            </div>
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-500">Server Version:</span>
              <span className="text-amber-400 font-mono">{health?.database.version || '8.0.41'}</span>
            </div>
          </div>

          {/* Card 3: Security & Driver */}
          <div className="bg-slate-950/60 p-6 rounded-xl border border-slate-800 space-y-4 hover:border-slate-700 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Integration & Security</span>
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-white">InnoDB / JWT</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300 font-mono">PyMySQL</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">Argon2 / Bcrypt • Alembic • DECIMAL(12,2)</p>
            </div>
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-500">Isolation & Pooling:</span>
              <span className="text-emerald-400 font-medium">Pool Size 10 • Pre-Ping</span>
            </div>
          </div>
        </div>

        {/* Live Status Response Inspector */}
        <div className="bg-slate-950/80 rounded-xl border border-slate-800 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-indigo-400" />
              <h3 className="font-semibold text-sm text-slate-200">
                Live Backend Diagnostic Probe (/api/v1/health)
              </h3>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Last probe: {lastChecked.toLocaleTimeString()}
            </span>
          </div>

          {loading ? (
            <div className="p-4 rounded-lg bg-slate-900 text-slate-400 text-xs font-mono flex items-center space-x-2">
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Probing API and executing SELECT VERSION()...</span>
            </div>
          ) : error ? (
            <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs font-mono">
              Error connecting to backend: {error}
            </div>
          ) : (
            <pre className="p-4 rounded-lg bg-slate-900 text-emerald-400 text-xs font-mono overflow-x-auto border border-slate-800">
              {JSON.stringify(health, null, 2)}
            </pre>
          )}
        </div>

        {/* 12-Phase Roadmap Progress Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Full Implementation Roadmap</h3>
              <p className="text-xs text-slate-400">Strict sequential phase execution as specified</p>
            </div>
            <span className="text-xs font-mono text-indigo-400 bg-indigo-950 px-2.5 py-1 rounded border border-indigo-800/60">
              1 of 12 Phases Active
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { num: '01', title: 'Project Setup & MySQL', status: 'COMPLETED', desc: 'FastAPI, MySQL 8.0, PyMySQL, Vite, React TS' },
              { num: '02', title: 'Auth & RBAC Schema', status: 'NEXT', desc: 'Admin, Staff, Customer JWT & reset tokens' },
              { num: '03', title: 'Customer Management', status: 'PENDING', desc: 'CRUD, search, filter, pagination, user linking' },
              { num: '04', title: 'Product & Variants', status: 'PENDING', desc: 'Multi-variant pricing calculation engine' },
              { num: '05', title: 'Subscription Plans', status: 'PENDING', desc: 'Billing intervals, rules, auto-close configs' },
              { num: '06', title: 'Quotation Management', status: 'PENDING', desc: 'Templates, pricing lines, conversion guard' },
              { num: '07', title: 'Subscription Lifecycle', status: 'PENDING', desc: 'Draft->Active->Closed state machine' },
              { num: '08', title: 'Renewal Scheduler', status: 'PENDING', desc: 'Automated renewal & Member 2 idempotency' },
              { num: '09', title: 'Churn Radar', status: 'PENDING', desc: 'Risk scoring (0-100), behavioral signal metrics' },
              { num: '10', title: 'Time Machine', status: 'PENDING', desc: 'Append-only event audit & state reconstruction' },
              { num: '11', title: 'Customer Portal', status: 'PENDING', desc: 'Self-service dashboard & strict tenant checks' },
              { num: '12', title: 'Testing & Hardening', status: 'PENDING', desc: 'Pytest, Vitest, Playwright E2E verification' },
            ].map((phase) => (
              <div 
                key={phase.num}
                className={`p-4 rounded-xl border transition ${
                  phase.status === 'COMPLETED'
                    ? 'bg-indigo-950/40 border-indigo-700/80 shadow-md shadow-indigo-950/50'
                    : phase.status === 'NEXT'
                    ? 'bg-slate-900 border-indigo-500/60 ring-1 ring-indigo-500/30'
                    : 'bg-slate-950/40 border-slate-800/80 opacity-70'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-indigo-400">PHASE {phase.num}</span>
                  {phase.status === 'COMPLETED' ? (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                      DONE
                    </span>
                  ) : phase.status === 'NEXT' ? (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                      UP NEXT
                    </span>
                  ) : (
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-900 text-slate-500">
                      QUEUED
                    </span>
                  )}
                </div>
                <h4 className="font-semibold text-sm text-slate-100">{phase.title}</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">{phase.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        Brightloop Nexus Enterprise Platform • Coordinated Microservices • Member 1 Architecture
      </footer>
    </div>
  );
}

export default App;
