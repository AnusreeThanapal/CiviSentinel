import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MapPin, Clock, ShieldAlert, Cpu } from 'lucide-react';
import { Alert } from '../types';
import { TrustGauge } from './TrustGauge';
import { SignalInspector } from './SignalInspector';

interface AlertDetailModalProps {
  alert: Alert | null;
  onClose: () => void;
}

export const AlertDetailModal: React.FC<AlertDetailModalProps> = ({ alert, onClose }) => {
  if (!alert) return null;

  const formattedDate = new Date(alert.timestamp).toLocaleString();

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[1100] flex justify-end pointer-events-none">
        {/* Semi-transparent Backdrop overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm pointer-events-auto"
        />

        {/* Slide-in Glassmorphic Side Drawer */}
        <motion.div
          initial={{ x: '100%', opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '100%', opacity: 0 }}
          transition={{ type: 'spring', stiffness: 350, damping: 30 }}
          className="relative w-full max-w-md h-full glass-panel border-l border-white/10 shadow-2xl p-6 overflow-y-auto pointer-events-auto flex flex-col justify-between"
        >
          <div className="space-y-6">
            {/* Header & Close Button */}
            <div className="flex items-start justify-between pb-4 border-b border-white/10">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-sev-red/20 text-sev-red border border-sev-red/40">
                    HAZARD ALERT
                  </span>
                  <span className="font-mono text-xs text-slate-400">{alert.alert_id}</span>
                </div>
                <h2 className="font-display text-xl font-bold uppercase text-slate-100 tracking-wide">
                  {alert.type.replace('_', ' ')}
                </h2>
              </div>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg bg-slate-800/80 text-slate-400 hover:text-slate-100 hover:bg-slate-700 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Location & Metadata Cards */}
            <div className="space-y-3">
              <div className="flex items-start space-x-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <MapPin className="w-5 h-5 text-ops-accent shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="font-sans text-sm font-semibold text-slate-200">
                    {alert.location.name}
                  </div>
                  <div className="font-mono text-xs text-slate-400">
                    LAT: {alert.location.lat.toFixed(4)} | LNG: {alert.location.lng.toFixed(4)}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-mono text-slate-300">
                <Clock className="w-4 h-4 text-ops-violet shrink-0" />
                <span>DETECTED AT: {formattedDate}</span>
              </div>
            </div>

            {/* Trust Score Radial Gauge & Reasoning Box */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="font-display text-xs font-bold uppercase tracking-wider text-slate-300">
                    SPARK TRUST SCORE
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono">
                    Correlated confidence index
                  </p>
                </div>
                <TrustGauge score={alert.trust_score} size={85} />
              </div>

              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 space-y-1">
                <div className="flex items-center space-x-1.5 text-[10px] font-mono text-ops-accent uppercase tracking-wider font-semibold">
                  <Cpu className="w-3.5 h-3.5" />
                  <span>SYNTHESIZED REASONING TRACE</span>
                </div>
                <p className="text-xs font-sans text-slate-200 leading-relaxed font-medium">
                  "{alert.reasoning}"
                </p>
              </div>
            </div>

            {/* Contributing Signals Breakdown */}
            <div className="space-y-2">
              <div className="font-display text-xs font-bold uppercase tracking-wider text-slate-300">
                CONTRIBUTING RAW SIGNALS
              </div>
              <SignalInspector signals={alert.contributing_signals} />
            </div>
          </div>

          {/* Footer Action */}
          <div className="pt-6 border-t border-white/10">
            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-lg bg-ops-card hover:bg-slate-800 text-slate-200 font-mono text-xs font-semibold border border-white/10 transition-colors"
            >
              CLOSE DRAWER
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
