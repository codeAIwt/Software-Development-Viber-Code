# AI检测功能配置与使用指南

## 功能概述

本项目引入AI检测功能，用于检测用户是否在摄像头前方，防止用户在自习室中但人不在的情况。当检测到用户不在摄像头前方时，系统会自动将用户从自习室中退出。

## 技术方案

### 1. 前端实现

- 使用Canvas进行摄像头画面截图
- 每1分钟（可配置）截取一次摄像头画面
- 将截图发送到后端进行AI分析
- 根据分析结果决定是否将用户从自习室中退出

### 2. 后端实现

- 接收前端发送的截图
- 使用AI模型分析画面中是否有人
- 返回分析结果给前端
- 当检测到无人时，调用退出房间API

## 配置方法

### 1. 前端配置

在 `frontend/src/views/StudyRoomDetail.vue` 文件中，配置以下参数：

```javascript
// AI检测配置
const aiDetectionInterval = ref(60000); // 检测间隔，单位毫秒，默认1分钟
const aiDetectionEnabled = ref(true); // 是否启用AI检测
const aiDetectionTimer = ref(null); // 检测定时器
```

### 2. 后端配置

#### 2.1 安装依赖

```bash
# 安装AI模型依赖
pip install tensorflow opencv-python

# 或使用PyTorch
pip install torch torchvision
```

#### 2.2 下载预训练模型

- 可以使用OpenCV的Haar级联分类器进行人脸检测
- 或使用更先进的模型如YOLO、SSD等

#### 2.3 配置AI检测服务

在 `backend/services/ai_service.py` 文件中实现AI检测逻辑：

```python
import cv2
import numpy as np


def detect_person(image_data):
    """
    检测图像中是否有人
    :param image_data: 图像数据
    :return: 是否有人
    """
    # 使用Haar级联分类器检测人脸
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # 转换图像数据
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 检测人脸
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    # 如果检测到人脸，返回True
    return len(faces) > 0
```

## 引入AI的方法

### 1. 前端引入

在 `StudyRoomDetail.vue` 文件中添加以下代码：

```javascript
// 初始化AI检测
function initAiDetection() {
  if (aiDetectionEnabled.value) {
    aiDetectionTimer.value = setInterval(async () => {
      await captureAndDetect();
    }, aiDetectionInterval.value);
  }
}

// 截图并检测
async function captureAndDetect() {
  if (!videoRef.value || !cameraOn.value) return;
  
  try {
    // 创建临时Canvas用于截图
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = videoRef.value.videoWidth || 640;
    tempCanvas.height = videoRef.value.videoHeight || 480;
    const tempCtx = tempCanvas.getContext('2d');
    
    // 绘制当前视频帧
    tempCtx.drawImage(videoRef.value, 0, 0, tempCanvas.width, tempCanvas.height);
    
    // 转换为Base64
    const base64Image = tempCanvas.toDataURL('image/jpeg');
    
    // 发送到后端进行检测
    const { data } = await studyRoomApi.detectPerson(base64Image);
    if (data.code === 200) {
      if (!data.data.has_person) {
        // 检测到无人，自动退出房间
        await onLeave();
      }
    }
  } catch (error) {
    console.error('AI检测失败:', error);
  }
}

// 组件挂载时初始化AI检测
onMounted(async () => {
  // 其他初始化代码...
  initAiDetection();
});

// 组件卸载时清除定时器
onUnmounted(() => {
  // 其他清理代码...
  if (aiDetectionTimer.value) {
    clearInterval(aiDetectionTimer.value);
  }
});
```

### 2. 后端引入

#### 2.1 创建AI检测服务

创建 `backend/services/ai_service.py` 文件，实现AI检测逻辑。

#### 2.2 创建AI检测API

在 `backend/controllers/room_controller.py` 文件中添加AI检测API：

```python
from fastapi import APIRouter, UploadFile, File
from services.ai_service import detect_person
from services.room_service import leave_room
from config.db import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post('/api/room/detect-person')
async def detect_person_api(
    image: str,
    room_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    检测摄像头前是否有人
    """
    try:
        # 处理Base64图像
        import base64
        image_data = base64.b64decode(image.split(',')[1])
        
        # 检测是否有人
        has_person = detect_person(image_data)
        
        if not has_person:
            # 检测到无人，自动退出房间
            leave_room(db, user_id, room_id)
        
        return {
            "code": 200,
            "data": {
                "has_person": has_person
            }
        }
    except Exception as e:
        return {
            "code": 500,
            "msg": f"检测失败: {str(e)}"
        }
```

#### 2.3 配置路由

在 `backend/app.py` 文件中添加AI检测路由：

```python
from controllers.room_controller import router as room_router

app.include_router(room_router)
```

## 隐私保护

- AI检测仅在本地进行，不上传用户图像到云端
- 检测完成后，图像数据会被立即销毁
- 检测结果仅用于判断用户是否在摄像头前，不做其他用途

## 性能优化

- 使用轻量级的AI模型，如Haar级联分类器，确保检测速度
- 调整检测间隔，避免过于频繁的检测影响系统性能
- 对图像进行压缩，减少传输数据量

## 故障处理

- 当AI检测失败时，系统会继续运行，不会影响自习室的正常使用
- 当网络连接不稳定时，系统会暂停AI检测，待网络恢复后重新开始

## 未来扩展

- 可以使用更先进的AI模型，如YOLOv5、MediaPipe等，提高检测准确率
- 可以添加姿态检测，判断用户是否在专注学习
- 可以添加行为分析，检测用户是否在做与学习无关的事情