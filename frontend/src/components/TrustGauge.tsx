import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface TrustGaugeProps {
  score: number; // 0.0 to 1.0
  size?: number; // Gauge diameter in px
  strokeWidth?: number;
  showLabel?: boolean;
}

export const TrustGauge: React.FC<TrustGaugeProps> = ({
  score,
  size = 90,
  strokeWidth = 8,
  showLabel = true
}) => {
  const [displayScore, setDisplayScore] = useState(0);

  // Animate numeric score count-up
  useEffect(() => {
    let start = 0;
    const end = Math.min(1.0, Math.max(0.0, score));
    const duration = 1000; // ms
    const startTime = performance.now();

    const updateCount = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1.0);
      // Ease out cubic
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(end * easedProgress);

      if (progress < 1.0) {
        requestAnimationFrame(updateCount);
      }
    };

    requestAnimationFrame(updateCount);
  }, [score]);

  // Radius and arc math
  const center = size / 2;
  const radius = center - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - displayScore * circumference;

  // Severity color selection
  let colorHex = '#00F2FE'; // Teal (< 0.4)
  let shadowGlow = 'rgba(0, 242, 254, 0.4)';
  if (score >= 0.7) {
    colorHex = '#FF3366'; // Red (> 0.7)
    shadowGlow = 'rgba(255, 51, 102, 0.5)';
  } else if (score >= 0.4) {
    colorHex = '#FFB800'; // Amber (0.4-0.7)
    shadowGlow = 'rgba(255, 184, 0, 0.4)';
  }

  return (
    <div className="relative flex flex-col items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Track Circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Animated Arc Circle */}
        <motion.circle
          cx={center}
          cy={center}
          r={radius}
          stroke={colorHex}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{
            filter: `drop-shadow(0 0 6px ${shadowGlow})`,
            transition: 'stroke-dashoffset 0.1s linear'
          }}
        />
      </svg>

      {/* Centered Score Display */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span
          className="font-mono font-bold tracking-tight"
          style={{
            fontSize: size > 80 ? '1.25rem' : '0.9rem',
            color: colorHex,
            textShadow: `0 0 10px ${shadowGlow}`
          }}
        >
          {displayScore.toFixed(2)}
        </span>
        {showLabel && (
          <span className="text-[9px] font-mono uppercase tracking-widest text-slate-400 -mt-0.5">
            TRUST
          </span>
        )}
      </div>
    </div>
  );
};
