/**
 * 视频流管理器 - 独立模块
 * 职责：摄像头管理、隐私处理、视频流输出
 * 与 WebRTC、信令、AI 检测完全解耦
 */

import { ref } from 'vue';

export const PrivacyMode = {
    OFF: 'off',
    BLUR: 'blur',
    HAND: 'hand'
};

let processedStream = null;
let animationFrameId = null;
let currentMode = 'off';
let currentVideoElement = null;
let currentCanvasElement = null;
let currentCtx = null;
let lastFrameTime = 0;
let targetFrameInterval = 1000 / 30;

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
            } catch (e) { }
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

    animationFrameId = requestAnimationFrame(drawFrame);
}

export function createVideoStreamManager() {
    const videoRef = ref(null);
    const canvasRef = ref(null);
    const localStream = ref(null);
    const cameraOn = ref(true);
    const cameraError = ref(false);
    const cameraLoading = ref(false);
    const privacyMode = ref(PrivacyMode.OFF);
    const cachedProcessedStream = ref(null);
    const cachedPrivacyMode = ref(PrivacyMode.OFF);

    async function initCamera() {
        cameraLoading.value = true;
        cameraError.value = false;
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('浏览器不支持摄像头功能');
            }
            if (localStream.value) {
                localStream.value.getTracks().forEach(track => track.stop());
            }
            cachedProcessedStream.value = null;
            cachedPrivacyMode.value = PrivacyMode.OFF;
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            if (videoRef.value) {
                videoRef.value.srcObject = stream;
            }
            localStream.value = stream;
        } catch (error) {
            cameraError.value = true;
            throw error;
        } finally {
            cameraLoading.value = false;
        }
    }

    function stopCamera() {
        if (localStream.value) {
            localStream.value.getTracks().forEach(track => track.stop());
            localStream.value = null;
        }
        stopProcessing();
        cameraOn.value = false;
        cachedProcessedStream.value = null;
        cachedPrivacyMode.value = PrivacyMode.OFF;
    }

    function stopProcessing() {
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
        if (processedStream) {
            processedStream.getTracks().forEach(track => track.stop());
            processedStream = null;
        }
        cachedProcessedStream.value = null;
        currentVideoElement = null;
        currentCanvasElement = null;
        currentCtx = null;
    }

    function setRefs(video, canvas) {
        videoRef.value = video;
        canvasRef.value = canvas;
    }

    function changePrivacyMode(mode) {
        privacyMode.value = mode;
        if (canvasRef.value && videoRef.value) {
            requestAnimationFrame(() => {
                if (canvasRef.value && videoRef.value) {
                    createProcessedStreamInternal(videoRef.value, canvasRef.value, mode);
                    cachedProcessedStream.value = null;
                }
            });
        }
    }

    function createProcessedStreamInternal(videoElement, canvasElement, mode) {
        if (!canvasElement) return null;

        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }

        if (processedStream) {
            processedStream.getTracks().forEach(track => track.stop());
            processedStream = null;
        }

        currentVideoElement = videoElement;
        currentCanvasElement = canvasElement;
        currentCtx = canvasElement.getContext('2d');
        currentMode = mode;
        lastFrameTime = 0;

        ensureCanvasSize();

        for (let i = 0; i < 5; i++) {
            drawFrame(i * targetFrameInterval);
        }

        processedStream = currentCanvasElement.captureStream(30);
        processedStream._isProcessed = true;
        processedStream._canvas = currentCanvasElement;

        return processedStream;
    }

    function getStreamForWebRTC() {
        if (privacyMode.value === PrivacyMode.OFF) {
            cachedProcessedStream.value = null;
            cachedPrivacyMode.value = PrivacyMode.OFF;
            return localStream.value;
        }

        if (canvasRef.value && videoRef.value) {
            if (cachedProcessedStream.value && cachedPrivacyMode.value === privacyMode.value) {
                return cachedProcessedStream.value;
            }
            cachedProcessedStream.value = createProcessedStreamInternal(videoRef.value, canvasRef.value, privacyMode.value);
            cachedPrivacyMode.value = privacyMode.value;
            return cachedProcessedStream.value;
        }

        return localStream.value;
    }

    function getLocalStream() {
        return localStream.value;
    }

    function getVideoRef() {
        return videoRef;
    }

    function getCanvasRef() {
        return canvasRef;
    }

    return {
        videoRef,
        canvasRef,
        localStream,
        cameraOn,
        cameraError,
        cameraLoading,
        privacyMode,
        privacyModes: [
            { value: PrivacyMode.OFF, label: '关闭隐私模式' },
            { value: PrivacyMode.BLUR, label: '模糊模式' },
            { value: PrivacyMode.HAND, label: '全屏遮挡模式' }
        ],
        setRefs,
        initCamera,
        stopCamera,
        changePrivacyMode,
        getStreamForWebRTC,
        getLocalStream,
        getVideoRef,
        getCanvasRef,
    };
}
