import React from 'react';
import { Radio, Newspaper, MessageSquare, User, Zap, Droplets } from 'lucide-react';
import { ContributingSignal } from '../types';

interface SignalInspectorProps {
  signals: ContributingSignal[];
}

export const SignalInspector: React.FC<SignalInspectorProps> = ({ signals }) => {
  if (!signals || signals.length === 0) {
    return (
      <div className="text-xs font-mono text-slate-500 py-3 italic text-center">
        No contributing raw signals recorded.
      </div>
    );
  }

  const sensorSignals = signals.filter(s => s.kind === 'sensor');
  const reportSignals = signals.filter(s => s.kind === 'report');

  return (
    <div className="space-y-4">
      {/* Sensor Readings Breakdown */}
      {sensorSignals.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs font-mono font-semibold text-ops-accent uppercase tracking-wider">
            <Radio className="w-3.5 h-3.5 text-ops-accent animate-pulse" />
            <span>Telemetry Sensors ({sensorSignals.length})</span>
          </div>

          <div className="grid grid-cols-1 gap-2">
            {sensorSignals.map((sig, idx) => {
              if (sig.kind !== 'sensor') return null;
              return (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-ops-accent/40 transition-colors"
                >
                  <div className="flex items-center space-x-2.5">
                    {sig.sensor_id.includes('WATER') ? (
                      <Droplets className="w-4 h-4 text-sev-cyan" />
                    ) : (
                      <Zap className="w-4 h-4 text-sev-amber" />
                    )}
                    <div>
                      <div className="font-mono text-xs font-bold text-slate-200">{sig.sensor_id}</div>
                      <div className="text-[10px] font-mono text-slate-400">HARDWARE TELEMETRY</div>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="font-mono text-sm font-bold text-ops-accent">
                      {sig.value}
                    </span>
                    <span className="font-mono text-xs text-slate-400 ml-1">{sig.unit}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Citizen & News Reports Breakdown */}
      {reportSignals.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs font-mono font-semibold text-ops-violet uppercase tracking-wider">
            <MessageSquare className="w-3.5 h-3.5 text-ops-violet" />
            <span>Citizen & News Reports ({reportSignals.length})</span>
          </div>

          <div className="space-y-2">
            {reportSignals.map((sig, idx) => {
              if (sig.kind !== 'report') return null;

              let SourceIcon = User;
              let sourceBadgeColor = 'bg-slate-800 text-slate-300 border-slate-700';

              if (sig.source_type === 'verified_news') {
                SourceIcon = Newspaper;
                sourceBadgeColor = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
              } else if (sig.source_type === 'social') {
                SourceIcon = MessageSquare;
                sourceBadgeColor = 'bg-sky-500/10 text-sky-300 border-sky-500/30';
              }

              return (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 hover:border-ops-violet/40 transition-colors"
                >
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-0.5 rounded flex items-center gap-1 border ${sourceBadgeColor}`}>
                        <SourceIcon className="w-3 h-3" />
                        <span className="capitalize">{sig.source_type.replace('_', ' ')}</span>
                      </span>
                    </div>

                    <span className="px-1.5 py-0.5 rounded font-bold bg-slate-800 text-ops-accent border border-white/10 uppercase">
                      {sig.language}
                    </span>
                  </div>

                  {/* Untranslated raw report text */}
                  <p className="text-xs text-slate-200 leading-relaxed font-sans pl-1 border-l-2 border-slate-700">
                    "{sig.text}"
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
