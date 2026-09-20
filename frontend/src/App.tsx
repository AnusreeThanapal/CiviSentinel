import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

import { WelcomePage } from './components/WelcomePage';
import { HeaderHealthBar } from './components/HeaderHealthBar';
import { LiveMap } from './components/LiveMap';
import { AlertFeed } from './components/AlertFeed';
import { AlertDetailModal } from './components/AlertDetailModal';
import { DemoControlPanel } from './components/DemoControlPanel';

import { Alert, SystemHealth, PipelineStage, DisruptionType, Language, SourceType } from './types';
import { CONFIG } from './config';
import { INITIAL_MOCK_ALERTS, INITIAL_MOCK_HEALTH, PRESET_SCENARIOS } from './services/mockData';
import { fetchAlerts, fetchSystemHealth, triggerSimulation } from './services/api';
import { wsService } from './services/websocket';

// Dashboard View Component (Untouched Existing Dashboard Layout)
function DashboardView() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [health, setHealth] = useState<SystemHealth>(INITIAL_MOCK_HEALTH);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const [pipelineStage, setPipelineStage] = useState<PipelineStage>('idle');
  const [stageMessage, setStageMessage] = useState<string>('');

  useEffect(() => {
    async function loadInitialData() {
      try {
        const initialAlerts = await fetchAlerts(50);
        setAlerts(initialAlerts);
        const initialHealth = await fetchSystemHealth();
        setHealth(initialHealth);
      } catch (e) {
        console.error('Error fetching initial data:', e);
        setAlerts(INITIAL_MOCK_ALERTS);
      }
    }
    loadInitialData();
  }, []);

  useEffect(() => {
    const unsubscribeConn = wsService.subscribeConnection((connected) => {
      setIsConnected(connected);
    });

    const unsubscribeAlerts = wsService.subscribeAlerts((incomingAlert) => {
      setAlerts((prevAlerts) => {
        if (prevAlerts.some((a) => a.alert_id === incomingAlert.alert_id)) {
          return prevAlerts;
        }
        return [incomingAlert, ...prevAlerts];
      });
    });

    return () => {
      unsubscribeConn();
      unsubscribeAlerts();
    };
  }, []);

  const handleInjectScenario = async (presetKey: keyof typeof PRESET_SCENARIOS) => {
    const preset = PRESET_SCENARIOS[presetKey];
    if (!preset) return;

    setPipelineStage('ingesting');
    setStageMessage(`Publishing synthetic raw events to Kafka raw topics...`);

    await new Promise((r) => setTimeout(r, 1200));

    setPipelineStage('correlating');
    setStageMessage(`Spark Structured Streaming evaluating 2m spatial grid window...`);

    await new Promise((r) => setTimeout(r, 1500));

    if (presetKey === 'UNVERIFIED_BELOW_THRESHOLD') {
      setPipelineStage('filtered');
      setStageMessage(`Trust Score ${preset.expectedScore.toFixed(2)} < 0.60 threshold. Event filtered (No alert).`);
      setTimeout(() => setPipelineStage('idle'), 4000);
      return;
    }

    const newAlertId = `ALT-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    const newAlert: Alert = {
      alert_id: newAlertId,
      type: preset.request.type,
      location: preset.request.location,
      trust_score: preset.expectedScore,
      reasoning: preset.expectedReasoning,
      contributing_signals: [
        ...preset.request.sensor_readings.map((s) => ({
          kind: 'sensor' as const,
          sensor_id: s.sensor_id,
          value: s.value,
          unit: s.unit
        })),
        ...preset.request.reports.map((r) => ({
          kind: 'report' as const,
          text: r.text,
          language: r.language,
          source_type: r.source_type
        }))
      ],
      timestamp: new Date().toISOString()
    };

    if (CONFIG.USE_MOCK_DATA) {
      wsService.emitMockAlert(newAlert);
    } else {
      await triggerSimulation(preset.request);
    }

    setPipelineStage('raised');
    setStageMessage(`SUCCESS: High-trust alert (${preset.expectedScore.toFixed(2)}) published to 'alerts' Kafka topic!`);
    setSelectedAlert(newAlert);
    setTimeout(() => setPipelineStage('idle'), 5000);
  };

  const handleCustomInject = async (
    type: DisruptionType,
    name: string,
    lat: number,
    lng: number,
    reportText: string,
    lang: Language,
    source: SourceType,
    sensorVal: number
  ) => {
    setPipelineStage('ingesting');
    setStageMessage(`Publishing custom raw event payload to Kafka...`);

    await new Promise((r) => setTimeout(r, 1200));

    setPipelineStage('correlating');
    setStageMessage(`Spark correlating custom events in spatial grid (${lat.toFixed(3)}, ${lng.toFixed(3)})...`);

    await new Promise((r) => setTimeout(r, 1500));

    const simulatedScore = source === 'verified_news' ? 0.88 : source === 'social' ? 0.72 : 0.45;
    
    if (simulatedScore < 0.6) {
      setPipelineStage('filtered');
      setStageMessage(`Trust Score ${simulatedScore.toFixed(2)} < 0.60 threshold. Event filtered.`);
      setTimeout(() => setPipelineStage('idle'), 4000);
      return;
    }

    const newAlert: Alert = {
      alert_id: `ALT-CUST-${Date.now()}`,
      type: type,
      location: { lat, lng, name },
      trust_score: simulatedScore,
      reasoning: `1 sensor reading (${sensorVal}) + 1 ${source} report in ${lang.toUpperCase()}, trust score ${simulatedScore.toFixed(2)}`,
      contributing_signals: [
        { kind: 'sensor', sensor_id: 'SENS-CUSTOM-01', value: sensorVal, unit: type === 'power_outage' ? 'volts' : 'meters' },
        { kind: 'report', text: reportText, language: lang, source_type: source }
      ],
      timestamp: new Date().toISOString()
    };

    if (CONFIG.USE_MOCK_DATA) {
      wsService.emitMockAlert(newAlert);
    } else {
      await triggerSimulation({
        type,
        location: { lat, lng, name },
        reports: [{ text: reportText, language: lang, source_type: source }],
        sensor_readings: [{ sensor_id: 'SENS-CUSTOM-01', value: sensorVal, unit: 'units' }]
      });
    }

    setPipelineStage('raised');
    setStageMessage(`ALERT RAISED: Published alert ${newAlert.alert_id} (Score: ${simulatedScore.toFixed(2)})`);
    setSelectedAlert(newAlert);
    setTimeout(() => setPipelineStage('idle'), 5000);
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-ops-base font-sans select-none">
      <HeaderHealthBar
        health={health}
        isConnected={isConnected}
        alertCount={alerts.length}
      />

      <div className="absolute inset-0 w-full h-full z-0">
        <LiveMap
          alerts={alerts}
          selectedAlert={selectedAlert}
          onSelectAlert={(alert) => setSelectedAlert(alert)}
        />
      </div>

      <div className="fixed top-20 right-4 bottom-4 z-[900] w-80 sm:w-96 pointer-events-none">
        <AlertFeed
          alerts={alerts}
          selectedAlert={selectedAlert}
          onSelectAlert={(alert) => setSelectedAlert(alert)}
        />
      </div>

      <DemoControlPanel
        onInjectScenario={handleInjectScenario}
        onCustomInject={handleCustomInject}
        currentStage={pipelineStage}
        stageMessage={stageMessage}
      />

      <AlertDetailModal
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
      />
    </div>
  );
}

// Wrapper for Welcome Page to supply navigation callback
function WelcomeWrapper() {
  const navigate = useNavigate();
  return <WelcomePage onGetStarted={() => navigate('/dashboard')} />;
}

// Animated Route Switcher Container
function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.35, ease: 'easeInOut' }}
              className="w-full h-full"
            >
              <WelcomeWrapper />
            </motion.div>
          }
        />
        <Route
          path="/dashboard"
          element={
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="w-full h-full"
            >
              <DashboardView />
            </motion.div>
          }
        />
      </Routes>
    </AnimatePresence>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AnimatedRoutes />
    </BrowserRouter>
  );
}

export default App;
