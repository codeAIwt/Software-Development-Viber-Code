import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet18
from PIL import Image
import io

# 加载预训练的ResNet-18模型
model = resnet18(pretrained=True)
model.eval()  # 设置为评估模式

# 图像预处理变换
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def detect_person(image_data):
    """
    使用ResNet-18模型检测图像中是否有人
    :param image_data: 图像数据 (字节流)
    :return: 是否有人
    """
    try:
        # 将字节流转换为PIL图像
        img = Image.open(io.BytesIO(image_data)).convert('RGB')

        # 预处理图像
        input_tensor = transform(img)
        input_batch = input_tensor.unsqueeze(0)  # 添加批次维度

        # 使用GPU（如果可用）
        if torch.cuda.is_available():
            input_batch = input_batch.to('cuda')
            model.to('cuda')

        # 进行预测
        with torch.no_grad():
            output = model(input_batch)

        # 获取预测结果
        _, predicted = torch.max(output, 1)

        # ImageNet类别中，人的类别编号是151-268（包括人、运动员等）
        # 这里简化处理，只要预测结果在这个范围内，就认为检测到人
        predicted_class = predicted.item()
        has_person = 151 <= predicted_class <= 268

        print(f"AI检测结果: {'有人' if has_person else '无人'}")
        return has_person
    except Exception as e:
        print(f"AI检测失败: {str(e)}")
        # 检测失败时默认返回True，避免误判
        return True