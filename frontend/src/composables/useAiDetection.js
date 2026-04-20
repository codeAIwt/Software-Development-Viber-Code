import { ref } from 'vue';

export function useAiDetection({ videoRef, enabled = true, intervalMs = 10000, detectFn, roomIdGetter, userIdGetter, onNoPerson }) {
    const aiTimer = ref(null);
    const aiEnabled = ref(enabled);

    async function captureAndDetect() {
        if (!videoRef.value) return;
        try {
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = videoRef.value.videoWidth || 640;
            tempCanvas.height = videoRef.value.videoHeight || 480;
            const tempCtx = tempCanvas.getContext('2d');
            tempCtx.drawImage(videoRef.value, 0, 0, tempCanvas.width, tempCanvas.height);
            const base64Image = tempCanvas.toDataURL('image/jpeg');
            const roomId = roomIdGetter();
            const userId = userIdGetter();
            if (!roomId || !userId) return;
            const { data } = await detectFn(base64Image, roomId, userId);
            if (data?.code === 200 && data.data && data.data.has_person === false) {
                onNoPerson?.();
            }
        } catch (err) {
            console.error('AI detection error', err);
        }
    }

    function start() {
        if (!aiEnabled.value) return;
        if (aiTimer.value) clearInterval(aiTimer.value);
        aiTimer.value = setInterval(async () => {
            await captureAndDetect();
        }, intervalMs);
    }

    function stop() {
        if (aiTimer.value) {
            clearInterval(aiTimer.value);
            aiTimer.value = null;
        }
    }

    return { aiTimer, aiEnabled, start, stop, captureAndDetect };
}
