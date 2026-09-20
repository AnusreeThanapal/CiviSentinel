import React from 'react';
import { motion } from 'framer-motion';
import { Activity, ShieldAlert, Cpu, Database, Wifi, WifiOff } from 'lucide-react';
import { SystemHealth } from '../types';
import { CONFIG } from '../config';

interface HeaderHealthBarProps {
  health: SystemHealth;
  isConnected: boolean;
  alertCount: number;
}

export const HeaderHealthBar: React.FC<HeaderHealthBarProps> = ({
  health,
  isConnected,
  alertCount
}) => {
  const formattedRetrainDate = health.model_last_retrained
    ? new Date(health.model_last_retrained).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : 'N/A';

  return (
    <header className="fixed top-3 left-4 right-4 z-[1000] pointer-events-auto">
      <div className="glass-panel rounded-xl px-4 py-2.5 flex items-center justify-between shadow-2xl backdrop-blur-xl border border-white/10">
        
        {/* Left: Brand Identity */}
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-ops-violet/20 border border-ops-violet/40">
            <ShieldAlert className="w-5 h-5 text-ops-accent animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-display text-sm font-bold tracking-wider text-slate-100 uppercase">
                CIVIC DISRUPTION EARLY-WARNING SYSTEM
              </h1>
              <span className="px-1.5 py-0.5 text-[10px] font-mono font-semibold rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                LIVE OPS
              </span>
            </div>
            <p className="text-[11px] font-mono text-slate-400">
              KAFKA + SPARK STRUCTURED STREAMING + AIRFLOW PIPELINE
            </p>
          </div>
        </div>

        {/* Center: System & Pipeline Telemetry */}
        <div className="hidden md:flex items-center space-x-6 text-xs font-mono">
          {/* Active Alerts Count */}
          <div className="flex items-center space-x-2 bg-slate-900/60 px-3 py-1 rounded-lg border border-slate-800">
            <Activity className="w-4 h-4 text-sev-amber" />
            <span className="text-slate-400">ACTIVE HAZARDS:</span>
            <span className="text-sev-amber font-bold text-sm">{alertCount}</span>
          </div>

          {/* Airflow Maintenance Status */}
          <div className="flex items-center space-x-2 bg-slate-900/60 px-3 py-1 rounded-lg border border-slate-800">
            <Database className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-400">DATA QUALITY:</span>
            <span className="text-emerald-400 font-semibold uppercase">{health.airflow_status}</span>
          </div>

          {/* Active Model Version */}
          <div className="flex items-center space-x-2 bg-slate-900/60 px-3 py-1 rounded-lg border border-slate-800">
            <Cpu className="w-4 h-4 text-ops-violet" />
            <span className="text-slate-400">MODEL RETRAINED:</span>
            <span className="text-slate-200">{formattedRetrainDate}</span>
          </div>
        </div>

        {/* Right: Connection LED Status & Mock Badge */}
        <div className="flex items-center space-x-3">
          {/* Mock Mode Indicator */}
          {CONFIG.USE_MOCK_DATA && (
            <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
              MOCK MODE (USE_MOCK_DATA=true)
            </span>
          )}

          {/* Connection Status LED */}
          <div className="flex items-center space-x-2 bg-slate-900/80 px-3 py-1 rounded-lg border border-white/10">
            <div className="relative flex items-center justify-center w-3 h-3">
              {isConnected ? (
                <>
                  <motion.div
                    className="absolute w-3 h-3 rounded-full bg-emerald-400"
                    animate={{ scale: [1, 1.8, 1], opacity: [0.8, 0.2, 0.8] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  />
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                </>
              ) : (
                <>
                  <motion.div
                    className="absolute w-3 h-3 rounded-full bg-rose-500"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                  />
                  <div className="w-2 h-2 rounded-full bg-rose-500" />
                </>
              )}
            </div>
            <span className="font-mono text-xs font-semibold text-slate-300">
              {isConnected ? (
                <span className="flex items-center gap-1 text-emerald-400">
                  <Wifi className="w-3 h-3" /> CONNECTED
                </span>
              ) : (
                <span className="flex items-center gap-1 text-rose-400">
                  <WifiOff className="w-3 h-3" /> RECONNECTING
                </span>
              )}
            </span>
          </div>
        </div>

      </div>
    </header>
  );
};
