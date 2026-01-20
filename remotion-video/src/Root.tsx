import React from 'react';
import { Composition, getInputProps } from 'remotion';
import { EducationalVideo } from './components/EducationalVideo';

interface DialogueLine {
  speaker_role: 'questioner' | 'explainer';
  speaker_name: string;
  line: string;
  start_frame: number;
  end_frame: number;
  emotion?: 'neutral' | 'happy' | 'surprised' | 'thinking' | 'excited';
}

interface VideoProps {
  dialogueLines: DialogueLine[];
  backgroundImage: string;
  audioFile: string;
  questionerName: string;
  explainerName: string;
  title: string;
  takeaway: string;
}

// Default props for preview in Remotion Studio
const defaultProps: VideoProps = {
  dialogueLines: [
    {
      speaker_role: 'questioner',
      speaker_name: 'Alex the Curious',
      line: 'Dr. Knowledge, why is the sky blue?',
      start_frame: 60,
      end_frame: 150,
    },
    {
      speaker_role: 'explainer',
      speaker_name: 'Dr. Knowledge',
      line: "Great question! It's all about how light interacts with our atmosphere.",
      start_frame: 150,
      end_frame: 270,
    },
  ],
  backgroundImage: 'https://images.unsplash.com/photo-1557683316-973673baf926?w=1080',
  audioFile: '',
  questionerName: 'Alex the Curious',
  explainerName: 'Dr. Knowledge',
  title: 'Why is the Sky Blue?',
  takeaway: 'Blue light gets scattered more by tiny air particles, making our sky appear blue!',
};

export const RemotionRoot: React.FC = () => {
  // Get input props passed from command line, or use defaults
  const inputProps = getInputProps() as Partial<VideoProps>;
  const props: VideoProps = { ...defaultProps, ...inputProps };

  // Calculate duration from dialogue lines
  const lastLine = props.dialogueLines[props.dialogueLines.length - 1];
  const contentDuration = lastLine ? lastLine.end_frame + 90 : 300; // Add 3 seconds for takeaway

  return (
    <>
      <Composition
        id="EducationalVideo"
        component={EducationalVideo as unknown as React.ComponentType<Record<string, unknown>>}
        durationInFrames={contentDuration}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={props as unknown as Record<string, unknown>}
      />
    </>
  );
};
