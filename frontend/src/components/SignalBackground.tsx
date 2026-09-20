import React from 'react';
import { motion } from 'framer-motion';

export const SignalBackground: React.FC = () => {
  // Pre-configured coordinates for ambient blooming radar rings across the grid
  const radarPoints = [
    { top: '22%', left: '18%', delay: 0 },
    { top: '65%', left: '25%', delay: 1.2 },
    { top: '35%', left: '75%', delay: 0.6 },
    { top: '78%', left: '82%', delay: 1.8 },
    { top: '50%', left: '50%', delay: 2.4 }
  ];

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
      {/* 1. Base Ambient Dark Canvas */}
      <div className="absolute inset-0 bg-[#080C10]" />

      {/* 2. City Grid Mesh Pattern Overlay */}
      <div 
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(0, 229, 255, 0.15) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(0, 229, 255, 0.15) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px'
        }}
      />

      {/* 3. Radial Gradient Vignette for Depth */}
      <div className="absolute inset-0 bg-radial-vignette" />

      {/* 4. Ambient Blooming Radar Pings */}
      {radarPoints.map((pt, idx) => (
        <div
          key={idx}
          className="absolute transform -translate-x-1/2 -translate-y-1/2"
          style={{ top: pt.top, left: pt.left }}
        >
          {/* Concentric Pulsing Ring */}
          <motion.div
            className="w-16 h-16 rounded-full border border-ops-accent/40"
            initial={{ scale: 0.3, opacity: 0.8 }}
            animate={{ scale: 2.8, opacity: 0 }}
            transition={{
              duration: 3.5,
              repeat: Infinity,
              delay: pt.delay,
              ease: 'easeOut'
            }}
          />
          {/* Core Dot */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-ops-accent/60" />
        </div>
      ))}

      {/* 5. Animated Data Trace Stream Lines */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Horizontal Light Trace */}
        <motion.div
          className="absolute h-[1px] w-48 bg-gradient-to-r from-transparent via-ops-accent to-transparent"
          style={{ top: '35%' }}
          initial={{ x: '-100%' }}
          animate={{ x: '100vw' }}
          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
        />
        {/* Vertical Light Trace */}
        <motion.div
          className="absolute w-[1px] h-48 bg-gradient-to-b from-transparent via-ops-violet to-transparent"
          style={{ left: '70%' }}
          initial={{ y: '-100%' }}
          animate={{ y: '100vh' }}
          transition={{ duration: 10, repeat: Infinity, ease: 'linear', delay: 2 }}
        />
      </div>

    </div>
  );
};
