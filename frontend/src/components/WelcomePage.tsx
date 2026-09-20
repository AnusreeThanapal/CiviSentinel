import React from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, ArrowRight, Activity, Cpu } from 'lucide-react';
import { SignalBackground } from './SignalBackground';

interface WelcomePageProps {
  onGetStarted: () => void;
}

export const WelcomePage: React.FC<WelcomePageProps> = ({ onGetStarted }) => {
  // Staggered animation container variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] }
    }
  };

  const titleWords = ["REAL-TIME", "CIVIC", "DISRUPTION", "EARLY-WARNING", "SYSTEM"];

  return (
    <div className="relative w-screen h-screen overflow-hidden flex flex-col items-center justify-between p-6 sm:p-12 select-none">
      
      {/* 1. Animated Signal Background */}
      <SignalBackground />

      {/* 2. Top Header Brand Bar */}
      <header className="relative z-10 w-full max-w-6xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-ops-violet/20 border border-ops-violet/40 shadow-glow-brand">
            <ShieldAlert className="w-5 h-5 text-ops-accent animate-pulse" />
          </div>
          <span className="font-display text-sm font-bold tracking-wider text-slate-100 uppercase">
            CIVIC-ALERT // OS
          </span>
        </div>

        <div className="flex items-center space-x-2 font-mono text-xs text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-white/10">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden sm:inline text-slate-400">STATUS:</span>
          <span className="text-emerald-400 font-semibold">ONLINE</span>
        </div>
      </header>

      {/* 3. Centered Main Hero Content */}
      <main className="relative z-10 max-w-4xl w-full text-center space-y-8 my-auto">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          {/* Eyebrow Tagline */}
          <motion.div variants={itemVariants} className="inline-flex items-center space-x-2">
            <span className="px-3 py-1 rounded-full text-xs font-mono font-bold tracking-widest text-ops-accent bg-ops-accent/10 border border-ops-accent/30 uppercase">
              CIVIC INTELLIGENCE · REAL-TIME MONITORING
            </span>
          </motion.div>

          {/* Main Title (Staggered Word Reveal) */}
          <motion.h1 
            variants={itemVariants} 
            className="font-display text-3xl sm:text-5xl md:text-6xl font-extrabold uppercase tracking-tight text-slate-100 leading-tight"
          >
            {titleWords.map((word, idx) => (
              <span 
                key={idx} 
                className={`inline-block mr-2 sm:mr-3 ${
                  word === 'EARLY-WARNING' ? 'text-transparent bg-clip-text bg-gradient-to-r from-ops-accent via-cyan-300 to-ops-violet' : ''
                }`}
              >
                {word}
              </span>
            ))}
          </motion.h1>

          {/* Description */}
          <motion.p 
            variants={itemVariants}
            className="font-sans text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed"
          >
            Watches live hardware sensor readings and multi-lingual citizen reports across the city in real time, correlating streams to raise early warnings before flooding, waterlogging, or power outages escalate.
          </motion.p>

          {/* "Get Started" CTA Button & Interactions */}
          <motion.div variants={itemVariants} className="pt-4 flex flex-col items-center space-y-4">
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.95 }}
              onClick={onGetStarted}
              className="relative group px-8 py-4 rounded-xl bg-ops-accent hover:bg-cyan-300 text-slate-950 font-display text-sm font-bold uppercase tracking-wider flex items-center space-x-3 transition-colors shadow-glow-brand cursor-pointer overflow-hidden"
            >
              {/* Hover Ripple Effect */}
              <span className="absolute inset-0 w-full h-full bg-white/20 transform -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out" />
              
              <span>ENTER COMMAND CENTER</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </motion.button>
          </motion.div>
        </motion.div>
      </main>

      {/* 4. Footer System Status Line */}
      <footer className="relative z-10 w-full max-w-6xl flex items-center justify-between text-xs font-mono text-slate-400 pt-6 border-t border-white/5">
        <div className="flex items-center space-x-2">
          <div className="relative flex items-center justify-center w-2.5 h-2.5">
            <motion.div
              className="absolute w-2.5 h-2.5 rounded-full bg-emerald-400"
              animate={{ scale: [1, 1.8, 1], opacity: [0.8, 0.2, 0.8] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            />
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          </div>
          <span>SYSTEM ONLINE · KAFKA & SPARK PIPELINE ACTIVE</span>
        </div>

        <div className="hidden sm:flex items-center space-x-4">
          <span className="flex items-center gap-1"><Cpu className="w-3.5 h-3.5 text-ops-violet" /> SPARK 3.5</span>
          <span>TAMIL & ENGLISH CORRELATION</span>
        </div>
      </footer>

    </div>
  );
};
