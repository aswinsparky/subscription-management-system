import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { Subscription } from '../../types/subscription';
import { TimelineEvent, StateSnapshot, SimulationResult } from '../../types/timemachine';
import { 
  History, 
  Play, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  Sparkles,
  Sliders
} from 'lucide-react';

export const TimeMachinePage: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [selectedSubId, setSelectedSubId] = useState<number | ''>('');
  const [selectedSub, setSelectedSub] = useState<Subscription | null>(null);

  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [reconstructedState, setReconstructedState] = useState<StateSnapshot | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // What-If Simulation
  const [simAction, setSimAction] = useState<string>('PAUSE');
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simLoading, setSimLoading] = useState<boolean>(false);

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/subscriptions', { params: { size: 100 } });
      const items: Subscription[] = res.data.items || [];
      setSubscriptions(items);
      if (items.length > 0 && !selectedSubId) {
        setSelectedSubId(items[0].id);
      }
    } catch (err) {
      console.error('Failed to load subscriptions', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSubscriptionHistory = async (subId: number) => {
    try {
      setLoading(true);
      const [subRes, timelineRes] = await Promise.all([
        apiClient.get<Subscription>(`/subscriptions/${subId}`),
        apiClient.get<TimelineEvent[]>(`/timemachine/subscriptions/${subId}/timeline`),
      ]);
      setSelectedSub(subRes.data);
      const events = timelineRes.data || [];
      setTimeline(events);
      if (events.length > 0) {
        // Start scrubber at latest event
        const latestIdx = events.length - 1;
        setCurrentStepIndex(latestIdx);
        replayToStep(events, latestIdx);
      } else {
        setReconstructedState(null);
      }
      setSimResult(null);
    } catch (err) {
      console.error('Failed to load subscription timeline', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscriptions();
  }, []);

  useEffect(() => {
    if (selectedSubId) {
      loadSubscriptionHistory(Number(selectedSubId));
    }
  }, [selectedSubId]);

  const replayToStep = (events: TimelineEvent[], stepIndex: number) => {
    if (!events.length || stepIndex < 0 || stepIndex >= events.length) return;
    const accumulated: any = {};
    for (let i = 0; i <= stepIndex; i++) {
      Object.assign(accumulated, events[i].new_state);
    }
    setReconstructedState(accumulated as StateSnapshot);
  };

  const handleSliderChange = (newIdx: number) => {
    setCurrentStepIndex(newIdx);
    replayToStep(timeline, newIdx);
  };

  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubId) return;
    try {
      setSimLoading(true);
      const res = await apiClient.post<SimulationResult>(
        `/timemachine/subscriptions/${selectedSubId}/simulate`,
        { action: simAction }
      );
      setSimResult(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Simulation failed.');
    } finally {
      setSimLoading(false);
    }
  };

  const currentEvent = timeline[currentStepIndex];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950/60 p-6 rounded-2xl border border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5 text-indigo-400 mb-1">
            <History className="w-5 h-5" />
            <h2 className="text-xl font-bold text-white tracking-wide">
              Subscription Time Machine & Event Reconstruction
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Replay state history at any point in time from the append-only ledger, and preview what-if policy transitions.
          </p>
        </div>

        {/* Subscription Target Selector */}
        <div className="flex items-center space-x-2 self-start md:self-auto">
          <label className="text-xs text-slate-400 font-medium">Target Subscription:</label>
          <select
            value={selectedSubId}
            onChange={(e) => setSelectedSubId(e.target.value ? Number(e.target.value) : '')}
            className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
          >
            {subscriptions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.subscription_number} &mdash; {s.customer?.full_name || `Cust #${s.customer_id}`} ({s.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && !selectedSub ? (
        <div className="p-12 text-center text-slate-500 text-xs">Loading time machine sequence...</div>
      ) : timeline.length === 0 ? (
        <div className="p-12 text-center text-slate-500 text-xs bg-slate-950/40 rounded-2xl border border-slate-800">
          No audit history events recorded for this subscription yet.
        </div>
      ) : (
        <>
          {/* Time Scrubber / Slider HUD */}
          <div className="bg-slate-950/70 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Timeline Time-Travel Scrubber
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  Step {currentStepIndex + 1} of {timeline.length}
                </span>
              </div>
              {currentEvent && (
                <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  <span>{new Date(currentEvent.timestamp).toLocaleString()}</span>
                  <span className="text-slate-600">&bull;</span>
                  <span className="text-indigo-400 font-bold">{currentEvent.event_type}</span>
                </div>
              )}
            </div>

            {/* Range Slider */}
            <div className="space-y-2">
              <input
                type="range"
                min={0}
                max={timeline.length - 1}
                value={currentStepIndex}
                onChange={(e) => handleSliderChange(parseInt(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer h-2 bg-slate-800 rounded-lg"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>{timeline[0]?.event_type} (Origin)</span>
                <span>Drag slider to travel back/forward in time</span>
                <span>{timeline[timeline.length - 1]?.event_type} (Latest Live)</span>
              </div>
            </div>
          </div>

          {/* Split Comparison: Reconstructed Past vs Live Now */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left: Reconstructed Historical State */}
            <div className="p-5 bg-slate-950/60 rounded-2xl border border-indigo-900/50 space-y-4 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-indigo-600 text-white text-[10px] font-mono px-3 py-1 rounded-bl-xl font-bold uppercase tracking-wider">
                Reconstructed State at Step {currentStepIndex + 1}
              </div>

              <div>
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                  Historical State Snapshot
                </span>
                <h3 className="text-lg font-bold text-white mt-1">
                  Status: {reconstructedState?.status || 'UNKNOWN'}
                </h3>
                <p className="text-xs text-slate-400">
                  Derived by replaying events up to{' '}
                  <strong className="text-slate-200">
                    {currentEvent ? new Date(currentEvent.timestamp).toLocaleDateString() : 'N/A'}
                  </strong>
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block mb-0.5">Recurring Amount</span>
                  <span className="font-mono font-bold text-indigo-300 text-sm">
                    ${reconstructedState?.total_amount || '0.00'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block mb-0.5">Interval</span>
                  <span className="font-mono font-semibold text-white">
                    {reconstructedState?.billing_interval || 'MONTHLY'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block mb-0.5">Period Start</span>
                  <span className="font-mono text-slate-300 text-[11px]">
                    {reconstructedState?.current_period_start
                      ? new Date(reconstructedState.current_period_start).toLocaleDateString()
                      : '&mdash;'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block mb-0.5">Period End</span>
                  <span className="font-mono text-slate-300 text-[11px]">
                    {reconstructedState?.current_period_end
                      ? new Date(reconstructedState.current_period_end).toLocaleDateString()
                      : '&mdash;'}
                  </span>
                </div>
              </div>

              {currentEvent && (
                <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800/80 text-xs space-y-1">
                  <div className="text-[11px] text-slate-400">
                    Applied Event: <strong className="text-white">{currentEvent.event_type}</strong> by{' '}
                    {currentEvent.actor_email} ({currentEvent.actor_role})
                  </div>
                  {currentEvent.reason && (
                    <div className="text-slate-300 italic text-[11px]">
                      &ldquo;{currentEvent.reason}&rdquo;
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right: Current Live State */}
            <div className="p-5 bg-slate-950/60 rounded-2xl border border-slate-800 space-y-4 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-emerald-600 text-white text-[10px] font-mono px-3 py-1 rounded-bl-xl font-bold uppercase tracking-wider">
                Live State (Real Time)
              </div>

              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                  Live Production State
                </span>
                <h3 className="text-lg font-bold text-white mt-1">
                  Status: {selectedSub?.status}
                </h3>
                <p className="text-xs text-slate-400">
                  Currently active in database for {selectedSub?.customer?.full_name}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block mb-0.5">Current Amount</span>
                  <span className="font-mono font-bold text-emerald-300 text-sm">
                    ${Number(selectedSub?.total_amount || 0).toFixed(2)}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block mb-0.5">Billing Interval</span>
                  <span className="font-mono font-semibold text-white">
                    {selectedSub?.billing_interval}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block mb-0.5">Current Period Start</span>
                  <span className="font-mono text-slate-300 text-[11px]">
                    {selectedSub ? new Date(selectedSub.current_period_start).toLocaleDateString() : '&mdash;'}
                  </span>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                  <span className="text-slate-400 block mb-0.5">Current Period End</span>
                  <span className="font-mono text-slate-300 text-[11px]">
                    {selectedSub ? new Date(selectedSub.current_period_end).toLocaleDateString() : '&mdash;'}
                  </span>
                </div>
              </div>

              <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800/80 text-xs">
                <span className="text-slate-400">Next Billing Date: </span>
                <span className="font-mono font-bold text-white">
                  {selectedSub ? new Date(selectedSub.next_billing_date).toLocaleDateString() : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Interactive What-If Simulator Sandbox */}
          <div className="p-6 bg-slate-950/70 rounded-2xl border border-indigo-900/40 shadow-xl space-y-4">
            <div className="flex items-center space-x-2 text-indigo-400">
              <Sparkles className="w-5 h-5 text-amber-300" />
              <h3 className="text-sm font-bold text-white tracking-wide uppercase">
                Predictive Sandbox & What-If Policy Simulator
              </h3>
            </div>
            <p className="text-xs text-slate-400">
              Evaluate simulated lifecycle actions against business rules without modifying production state.
            </p>

            <form onSubmit={handleRunSimulation} className="flex flex-wrap items-center gap-3">
              <select
                value={simAction}
                onChange={(e) => setSimAction(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="PAUSE">Simulate: PAUSE Contract</option>
                <option value="RESUME">Simulate: RESUME Contract</option>
                <option value="RENEW">Simulate: RENEW Contract Cycle</option>
                <option value="CANCEL">Simulate: CANCEL Contract</option>
                <option value="CLOSE">Simulate: CLOSE Contract Normally</option>
              </select>

              <button
                type="submit"
                disabled={simLoading}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/30 transition disabled:opacity-50 flex items-center space-x-1.5"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{simLoading ? 'Simulating...' : 'Run Simulation'}</span>
              </button>
            </form>

            {simResult && (
              <div
                className={`p-4 rounded-xl border text-xs space-y-3 ${
                  simResult.is_allowed
                    ? 'bg-emerald-950/30 border-emerald-800/80'
                    : 'bg-rose-950/30 border-rose-800/80'
                }`}
              >
                <div className="flex items-center space-x-2">
                  {simResult.is_allowed ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="font-bold text-emerald-300">
                        Simulation Allowed: Action &lsquo;{simResult.action}&rsquo; passes all policy rules!
                      </span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 text-rose-400" />
                      <span className="font-bold text-rose-300">
                        Simulation Rejected: {simResult.rejection_reason}
                      </span>
                    </>
                  )}
                </div>

                {/* Policy Checks Matrix */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
                  {Object.entries(simResult.policy_checks).map(([check, passed]) => (
                    <div
                      key={check}
                      className={`p-2 rounded-lg border flex items-center justify-between ${
                        passed
                          ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
                          : 'bg-rose-950/40 text-rose-300 border-rose-800/60'
                      }`}
                    >
                      <span className="truncate">{check}</span>
                      <span>{passed ? '✓' : '✗'}</span>
                    </div>
                  ))}
                </div>

                {simResult.predicted_state && (
                  <div className="p-3 bg-slate-900/60 rounded-lg text-xs text-slate-300 flex items-center space-x-2">
                    <span className="text-slate-400">Predicted Outcome:</span>
                    <span className="font-mono font-bold text-indigo-300">
                      Status &rarr; {simResult.predicted_state.status}
                    </span>
                    {simResult.predicted_state.next_billing_date && (
                      <span className="text-slate-400 text-[11px]">
                        (Next Billing: {new Date(simResult.predicted_state.next_billing_date).toLocaleDateString()})
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
