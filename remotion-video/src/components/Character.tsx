import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

interface CharacterProps {
  name: string;
  color: string;
  isSpeaking: boolean;
  isListening: boolean;
  position: 'left' | 'right';
  emotion?: 'neutral' | 'happy' | 'surprised' | 'thinking' | 'excited';
}

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

  // Breathing animation (subtle scale)
  const breathe = Math.sin(frame / fps * 1.5) * 0.02 + 1;

  // Speaking animation - more dynamic movement
  const speakBounce = isSpeaking
    ? Math.sin(frame / fps * 12) * 8 + Math.sin(frame / fps * 8) * 4
    : 0;

  // Mouth animation for speaking
  const mouthOpen = isSpeaking
    ? Math.abs(Math.sin(frame / fps * 10)) * 0.8 + 0.2
    : 0;

  // Head tilt when listening
  const headTilt = isListening
    ? Math.sin(frame / fps * 2) * 3
    : isSpeaking ? Math.sin(frame / fps * 4) * 2 : 0;

  // Eye blink (every ~3 seconds)
  const blinkCycle = (frame % (fps * 3)) / fps;
  const isBlinking = blinkCycle < 0.1;

  // Eyebrow animation based on emotion
  const eyebrowRaise = emotion === 'surprised' ? -8 :
                       emotion === 'happy' ? -3 :
                       emotion === 'thinking' ? 5 : 0;

  // Body lean toward other character when listening
  const bodyLean = isListening ? (position === 'left' ? 5 : -5) : 0;

  // Arm gesture when speaking
  const armGesture = isSpeaking ? Math.sin(frame / fps * 6) * 15 : 0;

  const isLeftPosition = position === 'left';
  const facingDirection = isLeftPosition ? 1 : -1;

  return (
    <div
      style={{
        position: 'absolute',
        [isLeftPosition ? 'left' : 'right']: 80,
        bottom: 400,
        transform: `
          scale(${breathe})
          translateY(${speakBounce}px)
          rotate(${bodyLean}deg)
          scaleX(${facingDirection})
        `,
        transformOrigin: 'bottom center',
      }}
    >
      {/* Character Body */}
      <svg width="280" height="400" viewBox="0 0 280 400">
        {/* Body */}
        <ellipse cx="140" cy="300" rx="80" ry="100" fill={color} />

        {/* Arms */}
        <g transform={`rotate(${armGesture}, 60, 250)`}>
          <ellipse cx="40" cy="280" rx="25" ry="50" fill={color} />
        </g>
        <g transform={`rotate(${-armGesture}, 220, 250)`}>
          <ellipse cx="240" cy="280" rx="25" ry="50" fill={color} />
        </g>

        {/* Head */}
        <g transform={`rotate(${headTilt}, 140, 120)`}>
          <ellipse cx="140" cy="100" rx="70" ry="75" fill={color} />

          {/* Eyes */}
          <g>
            {/* Left eye */}
            <ellipse
              cx="110"
              cy="85"
              rx={isBlinking ? 15 : 15}
              ry={isBlinking ? 2 : 20}
              fill="white"
            />
            {!isBlinking && (
              <circle cx="112" cy="88" r="8" fill="#333" />
            )}

            {/* Right eye */}
            <ellipse
              cx="170"
              cy="85"
              rx={isBlinking ? 15 : 15}
              ry={isBlinking ? 2 : 20}
              fill="white"
            />
            {!isBlinking && (
              <circle cx="168" cy="88" r="8" fill="#333" />
            )}
          </g>

          {/* Eyebrows */}
          <line
            x1="95" y1={60 + eyebrowRaise}
            x2="125" y2={65 + eyebrowRaise}
            stroke="#333"
            strokeWidth="4"
            strokeLinecap="round"
          />
          <line
            x1="155" y1={65 + eyebrowRaise}
            x2="185" y2={60 + eyebrowRaise}
            stroke="#333"
            strokeWidth="4"
            strokeLinecap="round"
          />

          {/* Mouth */}
          {isSpeaking ? (
            // Open mouth when speaking
            <ellipse
              cx="140"
              cy="135"
              rx={15 + mouthOpen * 10}
              ry={5 + mouthOpen * 15}
              fill="#c0392b"
            />
          ) : emotion === 'happy' || emotion === 'excited' ? (
            // Happy smile
            <path
              d="M 115 130 Q 140 160 165 130"
              fill="none"
              stroke="#333"
              strokeWidth="4"
              strokeLinecap="round"
            />
          ) : emotion === 'surprised' ? (
            // Surprised O mouth
            <ellipse cx="140" cy="135" rx="12" ry="15" fill="#c0392b" />
          ) : (
            // Neutral slight smile
            <path
              d="M 120 135 Q 140 145 160 135"
              fill="none"
              stroke="#333"
              strokeWidth="3"
              strokeLinecap="round"
            />
          )}

          {/* Glasses for Dr. Knowledge (check by color) */}
          {color === '#27ae60' && (
            <>
              <rect x="90" y="70" width="40" height="35" rx="5" fill="none" stroke="#333" strokeWidth="3" />
              <rect x="150" y="70" width="40" height="35" rx="5" fill="none" stroke="#333" strokeWidth="3" />
              <line x1="130" y1="87" x2="150" y2="87" stroke="#333" strokeWidth="3" />
            </>
          )}
        </g>
      </svg>

      {/* Name label */}
      <div
        style={{
          position: 'absolute',
          bottom: -40,
          left: '50%',
          transform: `translateX(-50%) scaleX(${facingDirection})`,
          color: 'white',
          fontSize: 24,
          fontWeight: 'bold',
          textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
          whiteSpace: 'nowrap',
        }}
      >
        {name}
      </div>
    </div>
  );
};
