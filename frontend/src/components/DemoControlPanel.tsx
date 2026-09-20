import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Sparkles, Send, CheckCircle, AlertOctagon, RefreshCw, X, ChevronDown } from 'lucide-react';
import { DisruptionType, Language, SourceType, PipelineStage, Alert } from '../types';
import { PRESET_SCENARIOS } from '../services/mockData';

interface DemoControlPanelProps {
  onInjectScenario: (presetKey: keyof typeof PRESET_SCENARIOS) => void;
  onCustomInject: (
    type: DisruptionType,
    name: string,
    lat: number,
    lng: number,
    reportText: string,
    lang: Language,
    source: SourceType,
    sensorVal: number
  ) => void;
  currentStage: PipelineStage;
  stageMessage: string;
}

export const DemoControlPanel: React.FC<DemoControlPanelProps> = ({
  onInjectScenario,
  onCustomInject,
  currentStage,
  stageMessage
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'presets' | 'custom'>('presets');

  // Custom Form State
  const [type, setType] = useState<DisruptionType>('flooding');
  const [locationName, setLocationName] = useState<string>('Anna Salai, Chennai');
  const [lat, setLat] = useState<number>(13.0604);
  const [lng, setLng] = useState<number>(80.2496);
  const [reportText, setReportText] = useState<string>('அண்ணா சாலையில் நீர் தேங்கியுள்ளது (Waterlogging near Anna Salai)');
  const [language, setLanguage] = useState<Language>('ta');
  const [sourceType, setSourceType] = useState<SourceType>('verified_news');
  const [sensorValue, setSensorValue] = useState<number>(4.2);

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCustomInject(type, locationName, lat, lng, reportText, language, sourceType, sensorValue);
  };

  // Pipeline Stepper Progress Stages
  const stages = [
    { id: 'ingesting', label: '1. INGESTED', desc: 'Kafka Raw Topics' },
    { id: 'correlating', label: '2. CORRELATING', desc: 'Spark 2m Window' },
    { id: 'completed', label: '3. PIPELINE RESULT', desc: 'Alert / Filtered' }
  ];

  const getStepStatusClass = (stepId: string) => {
    if (currentStage === 'idle') return 'border-slate-800 text-slate-500 bg-slate-900/40';

    if (stepId === 'ingesting') {
      if (currentStage === 'ingesting') return 'border-ops-accent bg-ops-accent/20 text-ops-accent animate-pulse';
      return 'border-emerald-500 bg-emerald-500/20 text-emerald-400';
    }

    if (stepId === 'correlating') {
      if (currentStage === 'ingesting') return 'border-slate-800 text-slate-500 bg-slate-900/40';
      if (currentStage === 'correlating') return 'border-ops-violet bg-ops-violet/20 text-ops-violet animate-pulse';
      return 'border-emerald-500 bg-emerald-500/20 text-emerald-400';
    }

    if (stepId === 'completed') {
      if (currentStage === 'raised') return 'border-sev-red bg-sev-red/20 text-sev-red font-bold';
      if (currentStage === 'filtered') return 'border-amber-500 bg-amber-500/20 text-amber-300 font-bold';
      return 'border-slate-800 text-slate-500 bg-slate-900/40';
    }

    return 'border-slate-800 text-slate-500';
  };

  return (
    <div className="fixed bottom-4 left-4 z-[1000] pointer-events-auto max-w-sm w-full">
      <div className="glass-panel rounded-xl border border-white/10 shadow-2xl overflow-hidden">
        
        {/* Toggle Bar */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full p-3 bg-slate-900/80 hover:bg-slate-800/80 transition-colors flex items-center justify-between border-b border-white/5"
        >
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-ops-accent animate-pulse" />
            <span className="font-display text-xs font-bold uppercase tracking-wider text-slate-100">
              DEMO CONTROL PANEL (SIMULATOR)
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-ops-accent/10 text-ops-accent border border-ops-accent/30 font-semibold">
              PIPELINE INJECTOR
            </span>
            <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </div>
        </button>

        {/* Live Pipeline Stepper Indicator (Always Visible) */}
        <div className="p-3 bg-slate-950/80 space-y-2 border-b border-white/5">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>PIPELINE EXECUTION STATE:</span>
            <span className="font-bold uppercase text-ops-accent">{currentStage}</span>
          </div>

          {/* Stepper Graphic */}
          <div className="grid grid-cols-3 gap-1.5">
            {stages.map((stg) => (
              <div
                key={stg.id}
                className={`p-1.5 rounded border text-center transition-all ${getStepStatusClass(stg.id)}`}
              >
                <div className="font-mono text-[9.5px] font-bold">{stg.label}</div>
                <div className="text-[8px] font-mono opacity-80">{stg.desc}</div>
              </div>
            ))}
          </div>

          {/* Stage Detail Message */}
          {stageMessage && (
            <div className="text-[11px] font-mono text-slate-300 bg-slate-900 p-2 rounded border border-slate-800 flex items-center space-x-1.5">
              <RefreshCw className={`w-3 h-3 text-ops-accent ${currentStage !== 'idle' && currentStage !== 'raised' && currentStage !== 'filtered' ? 'animate-spin' : ''}`} />
              <span className="line-clamp-1">{stageMessage}</span>
            </div>
          )}
        </div>

        {/* Expandable Injection Form & Presets */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="p-3.5 space-y-4 max-h-[60vh] overflow-y-auto"
            >
              {/* Tab Selector */}
              <div className="grid grid-cols-2 gap-1 p-1 bg-slate-900 rounded-lg border border-slate-800 font-mono text-xs">
                <button
                  onClick={() => setActiveTab('presets')}
                  className={`py-1.5 rounded font-semibold transition-colors ${
                    activeTab === 'presets'
                      ? 'bg-ops-accent text-slate-950 shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  PRESET SCENARIOS
                </button>
                <button
                  onClick={() => setActiveTab('custom')}
                  className={`py-1.5 rounded font-semibold transition-colors ${
                    activeTab === 'custom'
                      ? 'bg-ops-accent text-slate-950 shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  CUSTOM EVENT
                </button>
              </div>

              {/* Tab 1: Pre-scripted Scenarios */}
              {activeTab === 'presets' && (
                <div className="space-y-2.5">
                  <div className="text-[11px] font-mono text-slate-400">
                    Select a pre-scripted scenario to simulate live stream correlation:
                  </div>

                  {/* Preset 1 */}
                  <motion.button
                    whileTap={{ scale: 0.97 }}
                    onClick={() => onInjectScenario('HIGH_TRUST_FLOODING')}
                    className="w-full text-left p-3 rounded-lg bg-slate-900/80 hover:bg-slate-800/90 border border-sev-red/40 hover:border-sev-red transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs font-mono font-bold text-sev-red">
                      <span>SCENARIO 1: HIGH TRUST FLOODING</span>
                      <Play className="w-3.5 h-3.5" />
                    </div>
                    <p className="text-[11px] text-slate-300 font-sans">
                      2 sensors (5.3m) + 3 Tamil/English reports $\rightarrow$ Trust Score ~0.94
                    </p>
                  </motion.button>

                  {/* Preset 2 */}
                  <motion.button
                    whileTap={{ scale: 0.97 }}
                    onClick={() => onInjectScenario('UNVERIFIED_BELOW_THRESHOLD')}
                    className="w-full text-left p-3 rounded-lg bg-slate-900/80 hover:bg-slate-800/90 border border-amber-500/40 hover:border-amber-500 transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs font-mono font-bold text-amber-400">
                      <span>SCENARIO 2: SINGLE ANONYMOUS REPORT</span>
                      <Play className="w-3.5 h-3.5" />
                    </div>
                    <p className="text-[11px] text-slate-300 font-sans">
                      1 unverified social post $\rightarrow$ Trust Score ~0.20 (Filtered, No Alert)
                    </p>
                  </motion.button>

                  {/* Preset 3 */}
                  <motion.button
                    whileTap={{ scale: 0.97 }}
                    onClick={() => onInjectScenario('SENSOR_ONLY_POWER_OUTAGE')}
                    className="w-full text-left p-3 rounded-lg bg-slate-900/80 hover:bg-slate-800/90 border border-sev-amber/40 hover:border-sev-amber transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs font-mono font-bold text-sev-amber">
                      <span>SCENARIO 3: SENSOR-ONLY POWER OUTAGE</span>
                      <Play className="w-3.5 h-3.5" />
                    </div>
                    <p className="text-[11px] text-slate-300 font-sans">
                      2 telemetry sensors (0V collapse), 0 reports $\rightarrow$ Trust Score ~0.85
                    </p>
                  </motion.button>
                </div>
              )}

              {/* Tab 2: Custom Injection Form */}
              {activeTab === 'custom' && (
                <form onSubmit={handleCustomSubmit} className="space-y-3 font-mono text-xs">
                  <div>
                    <label className="text-slate-400 text-[10px] block mb-1">DISRUPTION TYPE</label>
                    <select
                      value={type}
                      onChange={(e) => setType(e.target.value as DisruptionType)}
                      className="w-full p-2 rounded bg-slate-900 border border-slate-800 text-slate-200"
                    >
                      <option value="flooding">Flooding</option>
                      <option value="waterlogging">Waterlogging</option>
                      <option value="power_outage">Power Outage</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-slate-400 text-[10px] block mb-1">LOCATION NAME</label>
                    <input
                      type="text"
                      value={locationName}
                      onChange={(e) => setLocationName(e.target.value)}
                      className="w-full p-2 rounded bg-slate-900 border border-slate-800 text-slate-200 font-sans"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-slate-400 text-[10px] block mb-1">LATITUDE</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={lat}
                        onChange={(e) => setLat(parseFloat(e.target.value))}
                        className="w-full p-2 rounded bg-slate-900 border border-slate-800 text-slate-200"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400 text-[10px] block mb-1">LONGITUDE</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={lng}
                        onChange={(e) => setLng(parseFloat(e.target.value))}
                        className="w-full p-2 rounded bg-slate-900 border border-slate-800 text-slate-200"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-slate-400 text-[10px] block mb-1">CITIZEN REPORT TEXT (TA/EN)</label>
                    <textarea
                      rows={2}
                      value={reportText}
                      onChange={(e) => setReportText(e.target.value)}
                      className="w-full p-2 rounded bg-slate-900 border border-slate-800 text-slate-200 font-sans text-xs"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-slate-400 text-[10px] block mb-1">LANGUAGE</label>
                      <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value as Language)}
                        className="w-full p-2 rounded bg-slate-900 border border-slate-800 text-slate-200"
                      >
                        <option value="ta">Tamil (ta)</option>
                        <option value="en">English (en)</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-slate-400 text-[10px] block mb-1">SOURCE TYPE</label>
                      <select
                        value={sourceType}
                        onChange={(e) => setSourceType(e.target.value as SourceType)}
                        className="w-full p-2 rounded bg-slate-900 border border-slate-800 text-slate-200"
                      >
                        <option value="verified_news">Verified News</option>
                        <option value="social">Social Media</option>
                        <option value="anonymous">Anonymous</option>
                      </select>
                    </div>
                  </div>

                  {/* Trigger Button with Tactile Animation */}
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    type="submit"
                    className="w-full py-2.5 rounded-lg bg-ops-accent hover:bg-cyan-400 text-slate-950 font-bold uppercase tracking-wider flex items-center justify-center space-x-2 transition-colors shadow-glow-brand mt-2"
                  >
                    <Send className="w-4 h-4" />
                    <span>INJECT CUSTOM EVENT</span>
                  </motion.button>
                </form>
              )}
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
};
