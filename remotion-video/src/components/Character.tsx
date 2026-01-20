import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

interface CharacterImages {
  neutral: string;
  talking: string;
}

type MovementType = 'idle' | 'talking' | 'walking' | 'waving' | 'pointing' | 'thinking' | 'reacting' | 'celebrating';

interface CharacterProps {
  name: string;
  color: string;
  isSpeaking: boolean;
  isListening: boolean;
  position: 'left' | 'right';
  emotion?: 'neutral' | 'happy' | 'surprised' | 'thinking' | 'excited';
  images?: CharacterImages;
}

// Determine movement type based on dialogue context
const getMovementFromContext = (isSpeaking: boolean, isListening: boolean, emotion: string): MovementType => {
  if (isSpeaking) {
    if (emotion === 'excited') return 'celebrating';
    if (emotion === 'thinking') return 'thinking';
    return 'talking';
  }
  if (isListening) {
    if (emotion === 'surprised') return 'reacting';
    if (emotion === 'thinking') return 'thinking';
    return 'idle';
  }
  return 'idle';
};

export const Character: React.FC<CharacterProps> = ({
  name,
  color,
  isSpeaking,
  isListening,
  position,
  emotion = 'neutral',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isLeftPosition = position === 'left';
  const cycle = frame / fps;

  // Get current movement type
  const movement = getMovementFromContext(isSpeaking, isListening, emotion);

  // Animation parameters based on movement
  const getAnimationParams = () => {
    switch (movement) {
      case 'talking':
        return {
          headBob: Math.sin(cycle * 6) * 5,
          leftArmAngle: -30 + Math.sin(cycle * 4) * 25,
          rightArmAngle: -150 + Math.sin(cycle * 4 + 1) * 20,
          bodyLean: Math.sin(cycle * 3) * 3,
          mouthOpen: Math.abs(Math.sin(cycle * 10)) * 0.8,
        };

      case 'waving':
        return {
          headBob: Math.sin(cycle * 2) * 3,
          leftArmAngle: -60,
          rightArmAngle: -160 + Math.sin(cycle * 8) * 30, // Waving arm
          bodyLean: 0,
          mouthOpen: 0.3,
        };

      case 'pointing':
        return {
          headBob: 0,
          leftArmAngle: -70,
          rightArmAngle: -180, // Pointing straight
          bodyLean: 5,
          mouthOpen: 0,
        };

      case 'thinking':
        return {
          headBob: Math.sin(cycle * 1) * 2,
          leftArmAngle: -60,
          rightArmAngle: -45, // Hand on chin
          bodyLean: -5,
          mouthOpen: 0,
        };

      case 'reacting':
        return {
          headBob: Math.sin(cycle * 8) * 8,
          leftArmAngle: -120 + Math.sin(cycle * 6) * 15,
          rightArmAngle: -60 + Math.sin(cycle * 6) * 15,
          bodyLean: Math.sin(cycle * 4) * 5,
          mouthOpen: 0.6,
        };

      case 'celebrating':
        return {
          headBob: Math.abs(Math.sin(cycle * 6)) * 10,
          leftArmAngle: -150 + Math.sin(cycle * 5) * 20,
          rightArmAngle: -30 + Math.sin(cycle * 5 + Math.PI) * 20,
          bodyLean: Math.sin(cycle * 4) * 5,
          mouthOpen: 0.7,
        };

      default: // idle
        return {
          headBob: Math.sin(cycle * 1.5) * 2,
          leftArmAngle: -70 + Math.sin(cycle * 1) * 5,
          rightArmAngle: -110 + Math.sin(cycle * 1) * 5,
          bodyLean: 0,
          mouthOpen: 0,
        };
    }
  };

  const anim = getAnimationParams();

  // Blinking
  const blinkCycle = (frame % Math.floor(fps * 3.5)) / fps;
  const isBlinking = blinkCycle < 0.08;

  // Character position
  const xPos = isLeftPosition ? 280 : 800;

  // Calculate arm endpoints
  const shoulderY = 120;
  const armLength = 70;

  const leftArmEnd = {
    x: 150 + Math.cos((anim.leftArmAngle * Math.PI) / 180) * armLength,
    y: shoulderY - Math.sin((anim.leftArmAngle * Math.PI) / 180) * armLength,
  };

  const rightArmEnd = {
    x: 150 + Math.cos((anim.rightArmAngle * Math.PI) / 180) * armLength,
    y: shoulderY - Math.sin((anim.rightArmAngle * Math.PI) / 180) * armLength,
  };

  // Stroke width for clean lines
  const strokeWidth = 6;

  return (
    <div
      style={{
        position: 'absolute',
        left: xPos,
        bottom: 400,
        transform: `translateX(-50%)`,
      }}
    >
      <svg
        width="300"
        height="350"
        viewBox="0 0 300 350"
        style={{ overflow: 'visible' }}
      >
        {/* Body lean transform */}
        <g transform={`rotate(${anim.bodyLean}, 150, 250)`}>

          {/* Head */}
          <g transform={`translate(0, ${anim.headBob})`}>
            {/* Head circle - outline only */}
            <circle
              cx="150"
              cy="50"
              r="40"
              fill="none"
              stroke="black"
              strokeWidth={strokeWidth}
            />

            {/* Eyes */}
            {isBlinking ? (
              // Blinking - horizontal lines
              <>
                <line x1="130" y1="45" x2="142" y2="45" stroke="black" strokeWidth="3" strokeLinecap="round" />
                <line x1="158" y1="45" x2="170" y2="45" stroke="black" strokeWidth="3" strokeLinecap="round" />
              </>
            ) : (
              // Open eyes - simple dots
              <>
                <circle cx="136" cy="45" r="5" fill="black" />
                <circle cx="164" cy="45" r="5" fill="black" />
              </>
            )}

            {/* Mouth */}
            {anim.mouthOpen > 0.1 ? (
              // Open mouth - oval
              <ellipse
                cx="150"
                cy="70"
                rx={6 + anim.mouthOpen * 6}
                ry={3 + anim.mouthOpen * 10}
                fill="none"
                stroke="black"
                strokeWidth="3"
              />
            ) : (
              // Closed mouth - simple line or slight smile
              <path
                d="M 140 68 Q 150 75 160 68"
                fill="none"
                stroke="black"
                strokeWidth="3"
                strokeLinecap="round"
              />
            )}
          </g>

          {/* Neck */}
          <line
            x1="150"
            y1={90 + anim.headBob}
            x2="150"
            y2="110"
            stroke="black"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Body */}
          <line
            x1="150"
            y1="110"
            x2="150"
            y2="200"
            stroke="black"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Left Arm */}
          <line
            x1="150"
            y1={shoulderY}
            x2={leftArmEnd.x}
            y2={leftArmEnd.y}
            stroke="black"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Right Arm */}
          <line
            x1="150"
            y1={shoulderY}
            x2={rightArmEnd.x}
            y2={rightArmEnd.y}
            stroke="black"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Left Leg */}
          <line
            x1="150"
            y1="200"
            x2="120"
            y2="290"
            stroke="black"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Right Leg */}
          <line
            x1="150"
            y1="200"
            x2="180"
            y2="290"
            stroke="black"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
        </g>
      </svg>

      {/* Simple name label */}
      <div
        style={{
          position: 'absolute',
          bottom: 20,
          left: '50%',
          transform: 'translateX(-50%)',
          fontSize: 20,
          fontWeight: 'bold',
          color: 'black',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          whiteSpace: 'nowrap',
        }}
      >
        {name}
      </div>
    </div>
  );
};
