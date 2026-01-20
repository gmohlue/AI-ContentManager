import React from 'react';
import { AbsoluteFill, Audio, Img, useCurrentFrame, useVideoConfig, staticFile, Sequence, delayRender, continueRender } from 'remotion';
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

  // Determine emotions based on dialogue
  const getEmotion = (role: 'questioner' | 'explainer'): 'neutral' | 'happy' | 'surprised' | 'thinking' | 'excited' => {
    if (!currentLine) return 'neutral';
    if (currentLine.speaker_role !== role) {
      // Listening - show interest
      return currentLine.line.includes('?') ? 'thinking' : 'neutral';
    }
    // Speaking - match emotion to content
    const text = currentLine.line.toLowerCase();
    if (text.includes('!') || text.includes('great') || text.includes('amazing') || text.includes('wow')) {
      return 'excited';
    }
    if (text.includes('?')) return 'thinking';
    if (text.includes('exactly') || text.includes('perfect') || text.includes('yes')) return 'happy';
    return 'neutral';
  };

  // Title sequence (first 2 seconds)
  const showTitle = frame < fps * 2;
  const titleOpacity = showTitle
    ? Math.min(1, frame / (fps * 0.5)) * Math.max(0, 1 - (frame - fps * 1.5) / (fps * 0.5))
    : 0;

  // Takeaway sequence (last 3 seconds)
  const takeawayStart = durationInFrames - fps * 3;
  const showTakeaway = frame >= takeawayStart;
  const takeawayOpacity = showTakeaway
    ? Math.min(1, (frame - takeawayStart) / (fps * 0.5))
    : 0;

  // Use staticFile for assets served from public folder
  const bgSrc = backgroundImage.startsWith('http') ? backgroundImage : staticFile(backgroundImage);
  const audioSrc = audioFile ? (audioFile.startsWith('http') ? audioFile : staticFile(audioFile)) : '';

  return (
    <AbsoluteFill>
      {/* Background */}
      <Img
        src={bgSrc}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />

      {/* Gradient overlay for better text readability */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '50%',
          background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
        }}
      />

      {/* Audio */}
      {audioSrc && <Audio src={audioSrc} />}

      {/* Title card */}
      {titleOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '35%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            opacity: titleOpacity,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: 72,
              fontWeight: 'bold',
              color: 'white',
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
              marginBottom: 20,
            }}
          >
            {title}
          </div>
          <div
            style={{
              fontSize: 36,
              color: '#FFD700',
              textShadow: '0 2px 10px rgba(0,0,0,0.8)',
            }}
          >
            with {questionerName} & {explainerName}
          </div>
        </div>
      )}

      {/* Characters */}
      {!showTitle && (
        <>
          <Character
            name={questionerName}
            color="#3498db"
            isSpeaking={questionerSpeaking}
            isListening={explainerSpeaking}
            position="left"
            emotion={getEmotion('questioner')}
            images={questionerImages}
          />
          <Character
            name={explainerName}
            color="#27ae60"
            isSpeaking={explainerSpeaking}
            isListening={questionerSpeaking}
            position="right"
            emotion={getEmotion('explainer')}
            images={explainerImages}
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
            speakerColor={line.speaker_role === 'questioner' ? '#3498db' : '#27ae60'}
            startFrame={0}
            durationFrames={line.end_frame - line.start_frame}
          />
        </Sequence>
      ))}

      {/* Takeaway card */}
      {takeawayOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            opacity: takeawayOpacity,
            textAlign: 'center',
            padding: 40,
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            borderRadius: 20,
            maxWidth: width - 120,
            border: '3px solid #FFD700',
          }}
        >
          <div
            style={{
              fontSize: 36,
              color: '#FFD700',
              marginBottom: 20,
              fontWeight: 'bold',
            }}
          >
            Key Takeaway
          </div>
          <div
            style={{
              fontSize: 32,
              color: 'white',
              lineHeight: 1.5,
            }}
          >
            {takeaway}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
