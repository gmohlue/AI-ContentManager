import React from 'react';
import { AbsoluteFill, Audio, useCurrentFrame, useVideoConfig, staticFile, Sequence, interpolate } from 'remotion';
import { Character } from './Character';
import { DialogueBox } from './DialogueBox';

interface DialogueLine {
  speaker_role: 'questioner' | 'explainer';
  speaker_name: string;
  line: string;
  start_frame: number;
  end_frame: number;
  emotion?: 'neutral' | 'happy' | 'surprised' | 'thinking' | 'excited';
}

interface CharacterImages {
  neutral: string;
  talking: string;
}

interface VideoProps {
  dialogueLines: DialogueLine[];
  backgroundImage: string;
  audioFile: string;
  questionerName: string;
  explainerName: string;
  questionerImages?: CharacterImages;
  explainerImages?: CharacterImages;
  title: string;
  takeaway: string;
}

// Detect emotion from text content
const detectEmotion = (text: string): 'neutral' | 'happy' | 'surprised' | 'thinking' | 'excited' => {
  const lowerText = text.toLowerCase();

  if (lowerText.includes('!') && (lowerText.includes('wow') || lowerText.includes('amazing') || lowerText.includes('incredible'))) {
    return 'excited';
  }
  if (lowerText.includes('?')) {
    return 'thinking';
  }
  if (lowerText.includes('great') || lowerText.includes('exactly') || lowerText.includes('yes')) {
    return 'happy';
  }
  return 'neutral';
};

export const EducationalVideo: React.FC<VideoProps> = ({
  dialogueLines,
  backgroundImage,
  audioFile,
  questionerName,
  explainerName,
  questionerImages,
  explainerImages,
  title,
  takeaway,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  // Find current speaking character
  const currentLine = dialogueLines.find(
    (line) => frame >= line.start_frame && frame < line.end_frame
  );

  const questionerSpeaking = currentLine?.speaker_role === 'questioner';
  const explainerSpeaking = currentLine?.speaker_role === 'explainer';

  // Get emotions based on current dialogue
  const getCharacterEmotion = (role: 'questioner' | 'explainer'): 'neutral' | 'happy' | 'surprised' | 'thinking' | 'excited' => {
    if (!currentLine) return 'neutral';

    if (currentLine.speaker_role === role) {
      return detectEmotion(currentLine.line);
    } else {
      const text = currentLine.line.toLowerCase();
      if (text.includes('?')) return 'thinking';
      if (text.includes('!')) return 'surprised';
      return 'neutral';
    }
  };

  // Title sequence (first 2 seconds)
  const titleDuration = fps * 2;
  const showTitle = frame < titleDuration;
  const titleOpacity = interpolate(
    frame,
    [0, fps * 0.3, titleDuration - fps * 0.3, titleDuration],
    [0, 1, 1, 0],
    { extrapolateRight: 'clamp' }
  );

  // Takeaway sequence (last 3 seconds)
  const takeawayStart = durationInFrames - fps * 3;
  const showTakeaway = frame >= takeawayStart;
  const takeawayOpacity = interpolate(
    frame,
    [takeawayStart, takeawayStart + fps * 0.3],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  // Use staticFile for assets
  const audioSrc = audioFile ? (audioFile.startsWith('http') ? audioFile : staticFile(audioFile)) : '';

  return (
    <AbsoluteFill>
      {/* Pure white background */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background: 'white',
        }}
      />

      {/* Audio */}
      {audioSrc && <Audio src={audioSrc} />}

      {/* Simple Title card */}
      {showTitle && titleOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '40%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            opacity: titleOpacity,
            textAlign: 'center',
            width: width - 80,
          }}
        >
          <div
            style={{
              fontSize: 56,
              fontWeight: 'bold',
              color: 'black',
              fontFamily: 'system-ui, -apple-system, sans-serif',
            }}
          >
            {title}
          </div>
          <div
            style={{
              marginTop: 20,
              fontSize: 28,
              color: '#333',
              fontFamily: 'system-ui, -apple-system, sans-serif',
            }}
          >
            {questionerName} & {explainerName}
          </div>
        </div>
      )}

      {/* Characters - black outline stickmen */}
      {!showTitle && (
        <>
          <Character
            name={questionerName}
            color="black"
            isSpeaking={questionerSpeaking}
            isListening={explainerSpeaking}
            position="left"
            emotion={getCharacterEmotion('questioner')}
          />
          <Character
            name={explainerName}
            color="black"
            isSpeaking={explainerSpeaking}
            isListening={questionerSpeaking}
            position="right"
            emotion={getCharacterEmotion('explainer')}
          />
        </>
      )}

      {/* Dialogue boxes */}
      {dialogueLines.map((line, index) => (
        <Sequence
          key={index}
          from={line.start_frame}
          durationInFrames={line.end_frame - line.start_frame}
        >
          <DialogueBox
            speaker={line.speaker_name}
            text={line.line}
            speakerColor="black"
            startFrame={0}
            durationFrames={line.end_frame - line.start_frame}
          />
        </Sequence>
      ))}

      {/* Simple Takeaway card */}
      {showTakeaway && takeawayOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            opacity: takeawayOpacity,
            textAlign: 'center',
            padding: '35px 45px',
            backgroundColor: 'white',
            borderRadius: 16,
            maxWidth: width - 80,
            border: '4px solid black',
          }}
        >
          <div
            style={{
              fontSize: 28,
              color: 'black',
              marginBottom: 16,
              fontWeight: 'bold',
              fontFamily: 'system-ui, -apple-system, sans-serif',
            }}
          >
            Key Takeaway
          </div>
          <div
            style={{
              fontSize: 24,
              color: 'black',
              lineHeight: 1.5,
              fontFamily: 'system-ui, -apple-system, sans-serif',
            }}
          >
            {takeaway}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
