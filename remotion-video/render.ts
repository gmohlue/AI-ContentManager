import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import path from 'path';
import fs from 'fs';

interface DialogueLine {
  speaker_role: 'questioner' | 'explainer';
  speaker_name: string;
  line: string;
  start_frame: number;
  end_frame: number;
}

interface RenderConfig {
  dialogueLines: DialogueLine[];
  backgroundImage: string;
  audioFile: string;
  questionerName: string;
  explainerName: string;
  title: string;
  takeaway: string;
  outputPath: string;
}

async function renderVideo(configPath: string) {
  console.log('Reading config from:', configPath);
  const config: RenderConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

  // Copy assets to public folder for Remotion to serve
  const publicDir = path.resolve(__dirname, 'public');
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
  }

  // Copy background image
  const bgExt = path.extname(config.backgroundImage);
  const bgDest = path.join(publicDir, `background${bgExt}`);
  console.log('Copying background from:', config.backgroundImage);
  fs.copyFileSync(config.backgroundImage, bgDest);
  const staticBgPath = `background${bgExt}`;

  // Copy audio file
  const audioExt = path.extname(config.audioFile);
  const audioDest = path.join(publicDir, `audio${audioExt}`);
  console.log('Copying audio from:', config.audioFile);
  fs.copyFileSync(config.audioFile, audioDest);
  const staticAudioPath = `audio${audioExt}`;

  console.log('Bundling Remotion project...');
  const bundleLocation = await bundle({
    entryPoint: path.resolve(__dirname, 'src/index.ts'),
    webpackOverride: (config) => config,
    publicDir,
  });

  console.log('Selecting composition...');
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: 'EducationalVideo',
    inputProps: {
      dialogueLines: config.dialogueLines,
      backgroundImage: staticBgPath,
      audioFile: staticAudioPath,
      questionerName: config.questionerName,
      explainerName: config.explainerName,
      title: config.title,
      takeaway: config.takeaway,
    },
  });

  // Calculate duration from dialogue
  const lastLine = config.dialogueLines[config.dialogueLines.length - 1];
  const durationInFrames = lastLine ? lastLine.end_frame + 90 : 300;

  console.log(`Rendering video (${durationInFrames} frames)...`);
  await renderMedia({
    composition: {
      ...composition,
      durationInFrames,
    },
    serveUrl: bundleLocation,
    codec: 'h264',
    outputLocation: config.outputPath,
    inputProps: {
      dialogueLines: config.dialogueLines,
      backgroundImage: staticBgPath,
      audioFile: staticAudioPath,
      questionerName: config.questionerName,
      explainerName: config.explainerName,
      title: config.title,
      takeaway: config.takeaway,
    },
  });

  // Cleanup copied assets
  fs.unlinkSync(bgDest);
  fs.unlinkSync(audioDest);

  console.log('Video rendered successfully:', config.outputPath);
}

// Get config path from command line
const configPath = process.argv[2];
if (!configPath) {
  console.error('Usage: npx ts-node render.ts <config.json>');
  process.exit(1);
}

renderVideo(configPath).catch((err) => {
  console.error('Render failed:', err);
  process.exit(1);
});
