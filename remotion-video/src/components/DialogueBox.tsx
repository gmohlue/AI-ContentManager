import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

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
  const { fps, width } = useVideoConfig();

  const relativeFrame = frame - startFrame;

  // Simple fade in/out
  const fadeIn = interpolate(relativeFrame, [0, fps * 0.2], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const fadeOut = interpolate(
    relativeFrame,
    [durationFrames - fps * 0.2, durationFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const opacity = Math.min(fadeIn, fadeOut);

  // Typewriter effect
  const typewriterDuration = Math.min(durationFrames * 0.6, fps * 2);
  const charsToShow = Math.floor(
    interpolate(relativeFrame, [0, typewriterDuration], [0, text.length], {
      extrapolateRight: 'clamp',
    })
  );

  const displayText = text.slice(0, charsToShow);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 80,
        left: '50%',
        transform: 'translateX(-50%)',
        opacity,
        width: width - 60,
        maxWidth: 950,
      }}
    >
      {/* Minimal clean dialogue box */}
      <div
        style={{
          background: 'white',
          borderRadius: 12,
          padding: '20px 28px',
          border: '3px solid black',
        }}
      >
        {/* Speaker name */}
        <div
          style={{
            position: 'absolute',
            top: -14,
            left: 20,
            background: 'white',
            padding: '4px 16px',
            border: '3px solid black',
            borderRadius: 8,
          }}
        >
          <span
            style={{
              color: 'black',
              fontSize: 20,
              fontWeight: 'bold',
              fontFamily: 'system-ui, -apple-system, sans-serif',
            }}
          >
            {speaker}
          </span>
        </div>

        {/* Dialogue text */}
        <div
          style={{
            marginTop: 8,
            color: 'black',
            fontSize: 28,
            lineHeight: 1.4,
            fontWeight: 500,
            fontFamily: 'system-ui, -apple-system, sans-serif',
          }}
        >
          {displayText}
          {/* Simple cursor */}
          {charsToShow < text.length && (
            <span
              style={{
                display: 'inline-block',
                width: 2,
                height: 28,
                backgroundColor: 'black',
                marginLeft: 2,
                opacity: Math.sin(relativeFrame / fps * 10) > 0 ? 1 : 0,
                verticalAlign: 'middle',
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};
