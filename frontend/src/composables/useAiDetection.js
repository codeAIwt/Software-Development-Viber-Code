import { ref } from 'vue';

export function useAiDetection({ videoRef, enabled = true, intervalMs = 10000, detectFn, roomIdGetter, userIdGetter, onNoPerson, onDetectionResult }) {
    const aiTimer = ref(null);
    const aiEnabled = ref(enabled);
    const isStopping = ref(false);
    const consecutiveNoPersonCount = ref(0);
    const REQUIRED_CONSECUTIVE_DETECTIONS = 3;
    const lastDetectionResult = ref({ hasPerson: true, timestamp: Date.now() });
    const isDetecting = ref(false);

    async function captureAndDetect() {
        if (!aiEnabled.value) {
            return;
        }
        if (!videoRef.value) {
            return;
        }
        if (videoRef.value.readyState < 2) {
            return;
        }
        isDetecting.value = true;
        try {
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = videoRef.value.videoWidth || 640;
            tempCanvas.height = videoRef.value.videoHeight || 480;
            if (tempCanvas.width <= 0 || tempCanvas.height <= 0) {
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
                return;
            }
            const base64Image = tempCanvas.toDataURL('image/jpeg');
            if (!base64Image || base64Image.length < 100) {
                return;
            }
            const roomId = roomIdGetter();
            const userId = userIdGetter();
            if (!roomId || !userId) {
                return;
            }
            if (!aiEnabled.value || isStopping.value) {
                return;
            }

            console.log('[AI检测] calling API...');
            const { data } = await detectFn(base64Image, roomId, userId);
            console.log('[AI检测] API returned, has_person:', data?.data?.has_person);

            if (!aiEnabled.value || isStopping.value) {
                return;
            }
            if (data?.code === 200 && data.data) {
                lastDetectionResult.value = {
                    hasPerson: data.data.has_person,
                    timestamp: Date.now()
                };

                console.log('[AI检测] sending detection result to other users');
                onDetectionResult?.({
                    hasPerson: data.data.has_person,
                    timestamp: Date.now()
                });

                if (data.data.has_person === false) {
                    consecutiveNoPersonCount.value++;
                    console.log('[AI检测] no person detected, count:', consecutiveNoPersonCount.value);
                    if (consecutiveNoPersonCount.value >= REQUIRED_CONSECUTIVE_DETECTIONS) {
                        console.log('[AI检测] triggering onNoPerson');
                        consecutiveNoPersonCount.value = 0;
                        aiEnabled.value = false;
                        isDetecting.value = false;
                        onNoPerson?.();
                    }
                } else {
                    consecutiveNoPersonCount.value = 0;
                }
            }
        } catch (err) {
            consecutiveNoPersonCount.value = 0;
        } finally {
            if (aiEnabled.value) {
                isDetecting.value = false;
            }
        }
    }

    function start() {
        console.log('[AI检测] start called, aiEnabled:', aiEnabled.value);
        if (!aiEnabled.value) {
            return;
        }
        if (aiTimer.value) {
            return;
        }
        console.log('[AI检测] starting interval, intervalMs:', intervalMs);
        aiTimer.value = setInterval(async () => {
            await captureAndDetect();
        }, intervalMs);
    }

    function stop() {
        console.log('[AI检测] stop called');
        isStopping.value = true;
        aiEnabled.value = false;
        if (aiTimer.value) {
            clearInterval(aiTimer.value);
            aiTimer.value = null;
        }
        consecutiveNoPersonCount.value = 0;
        lastDetectionResult.value = { hasPerson: true, timestamp: Date.now() };
        isDetecting.value = false;
        setTimeout(() => { isStopping.value = false; }, 100);
    }

    return { aiTimer, aiEnabled, start, stop, captureAndDetect, lastDetectionResult, isDetecting, consecutiveNoPersonCount };
}
