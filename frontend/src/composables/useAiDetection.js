import { ref } from 'vue';

export function useAiDetection({ videoRef, enabled = true, intervalMs = 10000, detectFn, roomIdGetter, userIdGetter, onNoPerson }) {
    const aiTimer = ref(null);
    const aiEnabled = ref(enabled);
    const isStopping = ref(false);
    const consecutiveNoPersonCount = ref(0);
    const REQUIRED_CONSECUTIVE_DETECTIONS = 3;
    const lastDetectionResult = ref({ hasPerson: true, timestamp: Date.now() });
    const isDetecting = ref(false);

    async function captureAndDetect() {
        console.log('[AI检测] captureAndDetect 开始, aiEnabled=', aiEnabled.value, 'isDetecting=', isDetecting.value, 'count=', consecutiveNoPersonCount.value);
        if (!aiEnabled.value) {
            console.log('[AI检测] aiEnabled 为 false，直接返回');
            return;
        }
        if (!videoRef.value) {
            console.log('[AI检测] videoRef 不存在，直接返回');
            return;
        }
        if (videoRef.value.readyState < 2) {
            console.log('[AI检测] 视频尚未加载完成，跳过本次检测');
            return;
        }
        isDetecting.value = true;
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
            if (!roomId || !userId) {
                console.log('[AI检测] roomId 或 userId 不存在，直接返回');
                return;
            }
            if (!aiEnabled.value || isStopping.value) {
                console.log('[AI检测] aiEnabled 为 false 或正在停止，直接返回');
                return;
            }
            console.log('[AI检测] 调用API...');
            const { data } = await detectFn(base64Image, roomId, userId);
            console.log('[AI检测] API返回, data=', JSON.stringify(data), 'aiEnabled=', aiEnabled.value);
            if (!aiEnabled.value || isStopping.value) {
                console.log('[AI检测] aiEnabled 为 false 或正在停止，直接返回');
                return;
            }
            if (data?.code === 200 && data.data) {
                lastDetectionResult.value = {
                    hasPerson: data.data.has_person,
                    timestamp: Date.now()
                };
                console.log('[AI检测] has_person=', data.data.has_person, 'count=', consecutiveNoPersonCount.value);
                if (data.data.has_person === false) {
                    consecutiveNoPersonCount.value++;
                    console.log(`[AI检测] 第${consecutiveNoPersonCount.value}次检测到无人（需${REQUIRED_CONSECUTIVE_DETECTIONS}次）`);
                    if (consecutiveNoPersonCount.value >= REQUIRED_CONSECUTIVE_DETECTIONS) {
                        console.log(`[AI检测] 连续${REQUIRED_CONSECUTIVE_DETECTIONS}次检测到无人，触发离开房间`);
                        consecutiveNoPersonCount.value = 0;
                        aiEnabled.value = false;
                        isDetecting.value = false;
                        onNoPerson?.();
                    } else {
                        console.log(`[AI检测] 未达到${REQUIRED_CONSECUTIVE_DETECTIONS}次，不触发离开`);
                    }
                } else {
                    console.log('[AI检测] 检测到有人，重置计数');
                    consecutiveNoPersonCount.value = 0;
                }
            }
        } catch (err) {
            console.error('AI detection error', err);
            consecutiveNoPersonCount.value = 0;
        } finally {
            console.log('[AI检测] finally, aiEnabled=', aiEnabled.value, 'isDetecting=', isDetecting.value);
            if (aiEnabled.value) {
                isDetecting.value = false;
            }
        }
    }

    function start() {
        console.log('[AI检测] start() 被调用, aiEnabled=', aiEnabled.value, 'timer=', aiTimer.value);
        if (!aiEnabled.value) {
            console.log('[AI检测] start() 失败: aiEnabled 为 false');
            return;
        }
        if (aiTimer.value) {
            console.log('[AI检测] start() 失败: timer 已存在');
            return;
        }
        console.log('[AI检测] 启动定时器, intervalMs=', intervalMs);
        aiTimer.value = setInterval(async () => {
            await captureAndDetect();
        }, intervalMs);
    }

    function stop() {
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
