import React, { useEffect, useState } from 'react';
import { Lottie, LottieAnimationData } from '@remotion/lottie';
import { useCurrentFrame, useVideoConfig, staticFile } from 'remotion';

type AnimationState = 'idle' | 'talking' | 'thinking' | 'walking' | 'celebrating';

interface LottieCharacterProps {
  name: string;
  isSpeaking: boolean;
  isListening: boolean;
  position: 'left' | 'right';
  emotion?: 'neutral' | 'happy' | 'surprised' | 'thinking' | 'excited';
}

// Map of animation states to Lottie files
const ANIMATION_FILES: Record<AnimationState, string> = {
  idle: 'lottie/stickman-talking.json',
  talking: 'lottie/stickman-talking.json',
  thinking: 'lottie/thinking.json',
  walking: 'lottie/stickman-walking.json',
  celebrating: 'lottie/celebrating.json',
};

// Determine animation state based on character state
const getAnimationState = (
  isSpeaking: boolean,
  isListening: boolean,
  emotion: string
): AnimationState => {
  if (isSpeaking) {
    if (emotion === 'excited') return 'celebrating';
    return 'talking';
  }
  if (isListening) {
    if (emotion === 'thinking') return 'thinking';
    return 'idle';
  }
  return 'idle';
};

export const LottieCharacter: React.FC<LottieCharacterProps> = ({
  name,
  isSpeaking,
  isListening,
  position,
  emotion = 'neutral',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [animationData, setAnimationData] = useState<LottieAnimationData | null>(null);

  const isLeftPosition = position === 'left';
  const animationState = getAnimationState(isSpeaking, isListening, emotion);

  // Load animation data
  useEffect(() => {
    const loadAnimation = async () => {
      try {
        const response = await fetch(staticFile(ANIMATION_FILES[animationState]));
        const data = await response.json();
        setAnimationData(data);
      } catch (error) {
        console.error('Failed to load Lottie animation:', error);
      }
    };
    loadAnimation();
  }, [animationState]);

  // Character positioning
  const xPos = isLeftPosition ? 150 : 650;

  // Playback speed varies by state
  const playbackRate = isSpeaking ? 1.5 : 1;

  if (!animationData) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: xPos,
        bottom: 350,
        transform: `translateX(-50%) ${isLeftPosition ? '' : 'scaleX(-1)'}`,
      }}
    >
      <div
        style={{
          width: 300,
          height: 400,
        }}
      >
        <Lottie
          animationData={animationData}
          playbackRate={playbackRate}
          style={{
            width: '100%',
            height: '100%',
          }}
        />
      </div>

      {/* Name label */}
      <div
        style={{
          position: 'absolute',
          bottom: -20,
          left: '50%',
          transform: `translateX(-50%) ${isLeftPosition ? '' : 'scaleX(-1)'}`,
          fontSize: 22,
          fontWeight: 'bold',
          color: 'black',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          whiteSpace: 'nowrap',
          backgroundColor: 'white',
          padding: '4px 16px',
          borderRadius: 8,
          border: '2px solid black',
        }}
      >
        {name}
      </div>
    </div>
  );
};
