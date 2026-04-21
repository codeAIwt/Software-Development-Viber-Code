import { ref } from 'vue';

export function useAiDetection({ videoRef, enabled = true, intervalMs = 10000, detectFn, roomIdGetter, userIdGetter, onNoPerson }) {
    const aiTimer = ref(null);
    const aiEnabled = ref(enabled);
    const consecutiveNoPersonCount = ref(0);
    const REQUIRED_CONSECUTIVE_DETECTIONS = 1;

    async function captureAndDetect() {
        if (!videoRef.value) return;
        if (videoRef.value.readyState < 2) {
            console.log('[AI检测] 视频尚未加载完成，跳过本次检测');
            return;
        }
        try {
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = videoRef.value.videoWidth || 640;
            tempCanvas.height = videoRef.value.videoHeight || 480;
            if (tempCanvas.width <= 0 || tempCanvas.height <= 0) {
                console.log('[AI检测] 视频尺寸无效，跳过本次检测');
                return;
            }
            const tempCtx = tempCanvas.getContext('2d');
            tempCtx.drawImage(videoRef.value, 0, 0, tempCanvas.width, tempCanvas.height);
            const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
            const isBlank = imageData.data.every((value, index) => {
                if (index % 4 === 3) return true;
                return value === 0;
            });
            if (isBlank) {
                console.log('[AI检测] 画面为空白，跳过本次检测');
                return;
            }
            const base64Image = tempCanvas.toDataURL('image/jpeg');
            if (!base64Image || base64Image.length < 100) {
                console.log('[AI检测] 图片数据无效，跳过本次检测');
                return;
            }
            const roomId = roomIdGetter();
            const userId = userIdGetter();
            if (!roomId || !userId) return;
            const { data } = await detectFn(base64Image, roomId, userId);
            if (data?.code === 200 && data.data && data.data.has_person === false) {
                consecutiveNoPersonCount.value++;
                console.log(`[AI检测] 第${consecutiveNoPersonCount.value}次检测到无人`);
                if (consecutiveNoPersonCount.value >= REQUIRED_CONSECUTIVE_DETECTIONS) {
                    console.log('[AI检测] 连续多次检测到无人，触发离开房间');
                    consecutiveNoPersonCount.value = 0;
                    onNoPerson?.();
                }
            } else {
                consecutiveNoPersonCount.value = 0;
            }
        } catch (err) {
            console.error('AI detection error', err);
            consecutiveNoPersonCount.value = 0;
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
        consecutiveNoPersonCount.value = 0;
    }

    return { aiTimer, aiEnabled, start, stop, captureAndDetect };
}
