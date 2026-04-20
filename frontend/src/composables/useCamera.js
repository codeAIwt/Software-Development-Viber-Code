import { ref } from 'vue';
import { startCamera as startCameraApi, stopCamera as stopCameraApi, checkCameraPermission } from '../utils/video';

export function useCamera(videoRef, canvasRef, privacyMode) {
    const localStream = ref(null);
    const cameraOn = ref(true);
    const cameraError = ref(false);
    const cameraLoading = ref(false);

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
            applyPrivacyMode();
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
        } finally {
            localStream.value = null;
            cameraOn.value = false;
        }
    }

    function applyPrivacyMode() {
        if (!videoRef.value || !canvasRef.value) return;

        const video = videoRef.value;
        const canvas = canvasRef.value;
        const ctx = canvas.getContext('2d');

        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;

        let rafId = null;

        function draw() {
            if (!cameraOn.value) return;
            try {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                if (privacyMode.value === 'blur') {
                    ctx.filter = 'blur(10px)';
                    ctx.drawImage(canvas, 0, 0, canvas.width, canvas.height);
                    ctx.filter = 'none';
                } else if (privacyMode.value === 'hand') {
                    ctx.fillStyle = 'black';
                    ctx.fillRect(0, 0, canvas.width, canvas.height * 0.6);
                }
            } catch (err) {
                // ignore drawing errors
            }
            rafId = requestAnimationFrame(draw);
        }

        draw();

        return () => {
            if (rafId) cancelAnimationFrame(rafId);
        };
    }

    return {
        localStream,
        cameraOn,
        cameraError,
        cameraLoading,
        initCamera,
        stopCamera,
        applyPrivacyMode,
    };
}
