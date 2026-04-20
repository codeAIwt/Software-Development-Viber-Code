import cv2
import numpy as np
# import torch
# import torchvision.transforms as transforms
# from torchvision.models import resnet18
# from PIL import Image
# import io

# 加载预训练的ResNet-18模型
# model = resnet18(pretrained=True)
# model.eval()  # 设置为评估模式

# # 图像预处理变换
# transform = transforms.Compose([
#     transforms.Resize((224, 224)),
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
# ])

def detect_person(image_data):
    """
    使用 OpenCV Haar 级联分类器检测图像中是否有人脸
    :param image_data: 图像数据 (字节流)
    :return: 是否有人脸
    """
    try:
        # 加载 Haar 级联分类器
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # 将字节流转换为图像
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 转换为灰度图像
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 检测人脸
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # 如果检测到人脸，返回 True
        has_person = len(faces) > 0

        print(f"AI检测结果: {'有人' if has_person else '无人'}")
        return has_person
    except Exception as e:
        print(f"AI检测失败: {str(e)}")
        # 检测失败时默认返回 True，避免误判
        return True