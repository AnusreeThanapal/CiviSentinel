import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Droplet, Zap, Filter, SlidersHorizontal, ChevronRight, Clock } from 'lucide-react';
import { Alert, DisruptionType } from '../types';

interface AlertFeedProps {
  alerts: Alert[];
  selectedAlert: Alert | null;
  onSelectAlert: (alert: Alert) => void;
}

export const AlertFeed: React.FC<AlertFeedProps> = ({
  alerts,
  selectedAlert,
  onSelectAlert
}) => {
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [minTrust, setMinTrust] = useState<number>(0.0);
  const [showFilters, setShowFilters] = useState<boolean>(false);

  // Filter logic
  const filteredAlerts = alerts.filter((alert) => {
    if (typeFilter !== 'all' && alert.type !== typeFilter) return false;
    if (alert.trust_score < minTrust) return false;
    return true;
  });

  const getAlertIcon = (type: DisruptionType) => {
    switch (type) {
      case 'flooding':
        return <AlertTriangle className="w-4 h-4 text-sev-red" />;
      case 'waterlogging':
        return <Droplet className="w-4 h-4 text-sev-cyan" />;
      case 'power_outage':
        return <Zap className="w-4 h-4 text-sev-amber" />;
    }
  };

  const getSeverityBadgeClass = (score: number) => {
    if (score >= 0.7) return 'bg-sev-red/10 text-sev-red border-sev-red/30';
    if (score >= 0.4) return 'bg-sev-amber/10 text-sev-amber border-sev-amber/30';
    return 'bg-sev-cyan/10 text-sev-cyan border-sev-cyan/30';
  };

  return (
    <div className="w-full h-full flex flex-col glass-panel rounded-xl border border-white/10 shadow-2xl overflow-hidden pointer-events-auto">
      
      {/* Header & Filter Controls */}
      <div className="p-3.5 border-b border-white/10 space-y-3 bg-slate-900/40">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-ops-accent animate-pulse" />
            <h2 className="font-display text-xs font-bold uppercase tracking-wider text-slate-200">
              REAL-TIME ALERT FEED ({filteredAlerts.length})
            </h2>
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-1.5 rounded-lg border text-xs font-mono transition-colors flex items-center gap-1 ${
              showFilters
                ? 'bg-ops-accent/20 border-ops-accent text-ops-accent'
                : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>FILTER</span>
          </button>
        </div>

        {/* Expandable Filter Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="space-y-3 pt-2 border-t border-slate-800 overflow-hidden"
            >
              {/* Type Filter Buttons */}
              <div className="flex items-center gap-1.5 flex-wrap">
                {['all', 'flooding', 'waterlogging', 'power_outage'].map((t) => (
                  <button
                    key={t}
                    onClick={() => setTypeFilter(t)}
                    className={`px-2 py-1 rounded text-[10px] font-mono uppercase tracking-wider transition-colors border ${
                      typeFilter === t
                        ? 'bg-ops-accent text-slate-950 font-bold border-ops-accent'
                        : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    {t.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {/* Minimum Trust Score Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-mono text-slate-400">
                  <span>MIN TRUST THRESHOLD:</span>
                  <span className="font-bold text-ops-accent">{minTrust.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.9"
                  step="0.1"
                  value={minTrust}
                  onChange={(e) => setMinTrust(parseFloat(e.target.value))}
                  className="w-full accent-ops-accent bg-slate-800 h-1 rounded appearance-none cursor-pointer"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Alert Feed Items List */}
      <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-8 font-mono text-xs text-slate-500 italic">
            No alerts match current filter criteria.
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {filteredAlerts.map((alert) => {
              const isSelected = selectedAlert?.alert_id === alert.alert_id;
              const timeAgoMin = Math.max(0, Math.floor((Date.now() - new Date(alert.timestamp).getTime()) / 60000));

              return (
                <motion.div
                  key={alert.alert_id}
                  layout
                  initial={{ opacity: 0, y: -20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                  onClick={() => onSelectAlert(alert)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-slate-800/90 border-ops-accent shadow-glow-brand'
                      : 'bg-slate-900/60 border-slate-800/80 hover:bg-slate-800/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="p-1.5 rounded-md bg-slate-800 border border-slate-700 shrink-0">
                        {getAlertIcon(alert.type)}
                      </div>
                      <div>
                        <div className="font-display text-xs font-bold uppercase text-slate-200 tracking-wide">
                          {alert.type.replace('_', ' ')}
                        </div>
                        <div className="font-sans text-xs text-slate-300 line-clamp-1 font-medium">
                          {alert.location.name}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col items-end space-y-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${getSeverityBadgeClass(alert.trust_score)}`}>
                        {alert.trust_score.toFixed(2)}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500 flex items-center gap-0.5">
                        <Clock className="w-2.5 h-2.5" />
                        {timeAgoMin}m ago
                      </span>
                    </div>
                  </div>

                  {/* Reasoning Summary Preview */}
                  <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span className="line-clamp-1 text-[10.5px]">
                      {alert.contributing_signals.length} signal(s) correlated
                    </span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>

    </div>
  );
};
