/**
 * 视频处理工具 - 独立的隐私处理模块
 * 负责视频流的处理（模糊、手部遮挡等），与摄像头管理和WebRTC传输解耦
 * 采用稳定的帧率输出，模拟直播流的缓冲效果
 */

let processedStream = null;
let animationFrameId = null;
let currentMode = 'off';
let currentVideoElement = null;
let currentCanvasElement = null;
let currentCtx = null;
let lastFrameTime = 0;
let targetFrameInterval = 1000 / 30;
let frameCount = 0;

export const PrivacyMode = {
  OFF: 'off',
  BLUR: 'blur',
  HAND: 'hand'
};

function ensureCanvasSize() {
  if (currentVideoElement && currentCanvasElement) {
    if (currentVideoElement.videoWidth && currentVideoElement.videoHeight) {
      currentCanvasElement.width = currentVideoElement.videoWidth;
      currentCanvasElement.height = currentVideoElement.videoHeight;
    }
  }
}

function drawFrame(timestamp) {
  if (!currentCtx || !currentCanvasElement) {
    animationFrameId = requestAnimationFrame(drawFrame);
    return;
  }

  const elapsed = timestamp - lastFrameTime;
  if (elapsed < targetFrameInterval - 1) {
    animationFrameId = requestAnimationFrame(drawFrame);
    return;
  }

  lastFrameTime = timestamp - (elapsed % targetFrameInterval);
  ensureCanvasSize();

  const videoReady = currentVideoElement && currentVideoElement.readyState >= 2;

  if (currentMode === PrivacyMode.BLUR) {
    currentCtx.fillStyle = '#000000';
    currentCtx.fillRect(0, 0, currentCanvasElement.width, currentCanvasElement.height);
    if (videoReady) {
      try {
        currentCtx.drawImage(currentVideoElement, 0, 0, currentCanvasElement.width, currentCanvasElement.height);
        currentCtx.filter = 'blur(10px)';
        currentCtx.drawImage(currentCanvasElement, 0, 0, currentCanvasElement.width, currentCanvasElement.height);
        currentCtx.filter = 'none';
      } catch (e) {
        // Ignore draw errors during mode transitions
      }
    }
  } else if (currentMode === PrivacyMode.HAND) {
    currentCtx.fillStyle = '#000000';
    currentCtx.fillRect(0, 0, currentCanvasElement.width, currentCanvasElement.height);
  } else {
    if (videoReady) {
      try {
        currentCtx.drawImage(currentVideoElement, 0, 0, currentCanvasElement.width, currentCanvasElement.height);
      } catch (e) {
        currentCtx.fillStyle = '#000000';
        currentCtx.fillRect(0, 0, currentCanvasElement.width, currentCanvasElement.height);
      }
    } else {
      currentCtx.fillStyle = '#000000';
      currentCtx.fillRect(0, 0, currentCanvasElement.width, currentCanvasElement.height);
    }
  }

  frameCount++;
  animationFrameId = requestAnimationFrame(drawFrame);
}

export function createProcessedStream(videoElement, canvasElement, mode = PrivacyMode.OFF) {
  console.log('[videoProcessor] createProcessedStream called, mode:', mode, 'canvas:', !!canvasElement);

  if (!canvasElement) {
    console.log('[videoProcessor] no canvas, returning null');
    return null;
  }

  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }

  if (processedStream) {
    console.log('[videoProcessor] stopping existing stream');
    processedStream.getTracks().forEach(track => track.stop());
    processedStream = null;
  }

  currentVideoElement = videoElement;
  currentCanvasElement = canvasElement;
  currentCtx = canvasElement.getContext('2d');
  currentMode = mode;
  lastFrameTime = 0;
  frameCount = 0;

  ensureCanvasSize();

  for (let i = 0; i < 5; i++) {
    drawFrame(i * targetFrameInterval);
  }

  processedStream = currentCanvasElement.captureStream(30);
  processedStream._isProcessed = true;
  processedStream._canvas = currentCanvasElement;
  console.log('[videoProcessor] new stream created, id:', processedStream.id);

  return processedStream;
}

export function setPrivacyMode(mode) {
  console.log('[videoProcessor] setPrivacyMode:', mode);
  currentMode = mode;
}

export function stopProcessedStream() {
  console.log('[videoProcessor] stopProcessedStream called, frameCount:', frameCount);
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
  if (processedStream) {
    processedStream.getTracks().forEach(track => track.stop());
    processedStream = null;
  }
  currentVideoElement = null;
  currentCanvasElement = null;
  currentCtx = null;
}

export function getProcessedStream() {
  return processedStream;
}

export function isProcessing() {
  return processedStream !== null;
}
