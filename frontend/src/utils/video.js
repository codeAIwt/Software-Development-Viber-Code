/** 视频 / 媒体工具 */

// 全局摄像头流对象
let cameraStream = null;

/**
 * 获取摄像头权限并启动摄像头
 * @param {HTMLVideoElement} videoElement - 视频元素
 * @returns {Promise<MediaStream>} 摄像头流
 */
export async function startCamera(videoElement) {
  try {
    // 检查navigator.mediaDevices是否存在
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('浏览器不支持摄像头功能');
    }

    // 获取摄像头权限
    const stream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: false
    });

    // 存储流对象
    cameraStream = stream;

    // 将流赋值给视频元素
    if (videoElement) {
      videoElement.srcObject = stream;
    }

    return stream;
  } catch (error) {
    console.error('获取摄像头失败:', error);
    throw error;
  }
}

/**
 * 停止摄像头
 */
export function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => {
      track.stop();
    });
    cameraStream = null;
  }
}

/**
 * 检查是否有摄像头权限
 * @returns {Promise<boolean>} 是否有摄像头权限
 */
export async function checkCameraPermission() {
  try {
    // 检查navigator.mediaDevices是否存在
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return false;
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: false
    });
    stream.getTracks().forEach(track => track.stop());
    return true;
  } catch {
    return false;
  }
}