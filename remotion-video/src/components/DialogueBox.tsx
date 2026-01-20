import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, spring } from 'remotion';

interface DialogueBoxProps {
  speaker: string;
  text: string;
  speakerColor: string;
  startFrame: number;
  durationFrames: number;
}

export const DialogueBox: React.FC<DialogueBoxProps> = ({
  speaker,
  text,
  speakerColor,
  startFrame,
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const relativeFrame = frame - startFrame;
  const progress = relativeFrame / durationFrames;

  // Entrance animation
  const slideIn = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  // Exit animation
  const exitProgress = Math.max(0, (relativeFrame - durationFrames + fps * 0.3) / (fps * 0.3));
  const slideOut = interpolate(exitProgress, [0, 1], [0, 100]);

  // Text typewriter effect
  const charsToShow = Math.floor(
    interpolate(relativeFrame, [0, Math.min(durationFrames * 0.7, fps * 2)], [0, text.length], {
      extrapolateRight: 'clamp',
    })
  );

  const displayText = text.slice(0, charsToShow);

  // Wrap text into lines
  const wrapText = (text: string, maxChars: number = 45): string[] => {
    const words = text.split(' ');
    const lines: string[] = [];
    let currentLine = '';

    for (const word of words) {
      if ((currentLine + ' ' + word).trim().length <= maxChars) {
        currentLine = (currentLine + ' ' + word).trim();
      } else {
        if (currentLine) lines.push(currentLine);
        currentLine = word;
      }
    }
    if (currentLine) lines.push(currentLine);
    return lines;
  };

  const lines = wrapText(displayText);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 60,
        left: '50%',
        transform: `translateX(-50%) translateY(${(1 - slideIn) * 50 + slideOut}px)`,
        opacity: interpolate(slideIn, [0, 1], [0, 1]) * interpolate(exitProgress, [0, 1], [1, 0]),
        width: width - 120,
        padding: '25px 40px',
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        borderRadius: 20,
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
        border: `3px solid ${speakerColor}`,
      }}
    >
      {/* Speaker name */}
      <div
        style={{
          color: speakerColor,
          fontSize: 32,
          fontWeight: 'bold',
          marginBottom: 15,
          textShadow: `0 0 20px ${speakerColor}`,
        }}
      >
        {speaker}
      </div>

      {/* Dialogue text */}
      <div
        style={{
          color: 'white',
          fontSize: 38,
          lineHeight: 1.4,
          fontWeight: 500,
        }}
      >
        {lines.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
        {/* Blinking cursor during typing */}
        {charsToShow < text.length && (
          <span
            style={{
              opacity: Math.sin(frame / fps * 8) > 0 ? 1 : 0,
              color: speakerColor,
            }}
          >
            |
          </span>
        )}
      </div>
    </div>
  );
};
