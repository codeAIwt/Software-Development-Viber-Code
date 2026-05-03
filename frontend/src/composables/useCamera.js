import { ref } from 'vue';
import { startCamera as startCameraApi, stopCamera as stopCameraApi, checkCameraPermission } from '../utils/video';
import { createProcessedStream, stopProcessedStream, PrivacyMode } from '../utils/videoProcessor';

export function useCamera() {
    const videoRef = ref(null);
    const canvasRef = ref(null);
    const localStream = ref(null);
    const cameraOn = ref(true);
    const cameraError = ref(false);
    const cameraLoading = ref(false);
    const privacyMode = ref(PrivacyMode.OFF);
    const cachedProcessedStream = ref(null);
    const cachedPrivacyMode = ref(PrivacyMode.OFF);

    const privacyModes = [
        { value: PrivacyMode.OFF, label: '关闭隐私模式' },
        { value: PrivacyMode.BLUR, label: '模糊模式' },
        { value: PrivacyMode.HAND, label: '全屏遮挡模式' }
    ];

    function setRefs(video, canvas) {
        videoRef.value = video;
        canvasRef.value = canvas;
    }

    async function initCamera() {
        cameraLoading.value = true;
        cameraError.value = false;
        try {
            const isSupported = await checkCameraPermission();
            if (!isSupported) {
                throw new Error('浏览器不支持摄像头功能');
            }
            const stream = await startCameraApi(videoRef.value);
            localStream.value = stream;
        } catch (error) {
            cameraError.value = true;
            throw error;
        } finally {
            cameraLoading.value = false;
        }
    }

    function stopCamera() {
        try {
            stopCameraApi();
            stopProcessedStream();
        } finally {
            localStream.value = null;
            cameraOn.value = false;
            cachedProcessedStream.value = null;
        }
    }

    function changePrivacyMode(mode) {
        console.log('[useCamera] changePrivacyMode:', mode);
        privacyMode.value = mode;
        if (canvasRef.value && videoRef.value) {
            requestAnimationFrame(() => {
                if (canvasRef.value && videoRef.value) {
                    createProcessedStream(videoRef.value, canvasRef.value, mode);
                    cachedProcessedStream.value = null;
                }
            });
        }
    }

    function getStreamForWebRTC() {
        console.log('[useCamera] getStreamForWebRTC called, privacyMode:', privacyMode.value);

        if (privacyMode.value === PrivacyMode.OFF) {
            cachedProcessedStream.value = null;
            cachedPrivacyMode.value = PrivacyMode.OFF;
            console.log('[useCamera] returning localStream:', localStream.value?.id);
            return localStream.value;
        }

        if (canvasRef.value && videoRef.value) {
            if (cachedProcessedStream.value && cachedPrivacyMode.value === privacyMode.value) {
                console.log('[useCamera] returning cachedProcessedStream:', cachedProcessedStream.value?.id);
                return cachedProcessedStream.value;
            }
            console.log('[useCamera] creating new processed stream, mode:', privacyMode.value);
            cachedProcessedStream.value = createProcessedStream(videoRef.value, canvasRef.value, privacyMode.value);
            cachedPrivacyMode.value = privacyMode.value;
            console.log('[useCamera] new processed stream id:', cachedProcessedStream.value?.id);
            return cachedProcessedStream.value;
        }

        console.log('[useCamera] returning localStream (fallback):', localStream.value?.id);
        return localStream.value;
    }

    return {
        videoRef,
        canvasRef,
        localStream,
        cameraOn,
        cameraError,
        cameraLoading,
        privacyMode,
        privacyModes,
        setRefs,
        initCamera,
        stopCamera,
        changePrivacyMode,
        getStreamForWebRTC,
    };
}
