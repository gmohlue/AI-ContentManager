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

interface CharacterImages {
  neutral: string;
  talking: string;
}

interface RenderConfig {
  dialogueLines: DialogueLine[];
  backgroundImage: string;
  audioFile: string;
  questionerName: string;
  explainerName: string;
  questionerImages?: CharacterImages;
  explainerImages?: CharacterImages;
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

  // Copy character images if provided
  let questionerImages: CharacterImages | undefined;
  let explainerImages: CharacterImages | undefined;
  const copiedImages: string[] = [];

  if (config.questionerImages) {
    const qNeutralDest = path.join(publicDir, 'questioner_neutral.png');
    const qTalkingDest = path.join(publicDir, 'questioner_talking.png');
    console.log('Copying questioner images');
    fs.copyFileSync(config.questionerImages.neutral, qNeutralDest);
    fs.copyFileSync(config.questionerImages.talking, qTalkingDest);
    questionerImages = { neutral: 'questioner_neutral.png', talking: 'questioner_talking.png' };
    copiedImages.push(qNeutralDest, qTalkingDest);
  }

  if (config.explainerImages) {
    const eNeutralDest = path.join(publicDir, 'explainer_neutral.png');
    const eTalkingDest = path.join(publicDir, 'explainer_talking.png');
    console.log('Copying explainer images');
    fs.copyFileSync(config.explainerImages.neutral, eNeutralDest);
    fs.copyFileSync(config.explainerImages.talking, eTalkingDest);
    explainerImages = { neutral: 'explainer_neutral.png', talking: 'explainer_talking.png' };
    copiedImages.push(eNeutralDest, eTalkingDest);
  }

  console.log('Bundling Remotion project...');
  const bundleLocation = await bundle({
    entryPoint: path.resolve(__dirname, 'src/index.ts'),
    webpackOverride: (config) => config,
    publicDir,
  });

  console.log('Selecting composition...');
  const inputProps = {
    dialogueLines: config.dialogueLines,
    backgroundImage: staticBgPath,
    audioFile: staticAudioPath,
    questionerName: config.questionerName,
    explainerName: config.explainerName,
    questionerImages,
    explainerImages,
    title: config.title,
    takeaway: config.takeaway,
  };

  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: 'EducationalVideo',
    inputProps,
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
    inputProps,
  });

  // Cleanup copied assets
  fs.unlinkSync(bgDest);
  fs.unlinkSync(audioDest);
  copiedImages.forEach(img => {
    try { fs.unlinkSync(img); } catch (e) { /* ignore */ }
  });

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
