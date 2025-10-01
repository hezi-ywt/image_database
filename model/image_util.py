import hashlib
import os
import mimetypes
from PIL import Image
import io
from datetime import datetime

def calculate_file_hash(file_path):
    """计算文件的SHA256哈希值"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"计算文件哈希失败: {e}")
        return None

def _load_image_from_input(image_input):
    """从不同输入类型加载PIL图像对象
    
    参数:
        image_input: 可以是以下类型之一：
            - str: 文件路径
            - PIL.Image: PIL图像对象
            - bytes: 图像二进制数据
            - io.BytesIO: 字节流对象
    
    返回:
        PIL.Image: 图像对象
    """
    if isinstance(image_input, str):
        # 文件路径
        return Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        # PIL图像对象
        return image_input
    elif isinstance(image_input, (bytes, bytearray)):
        # 二进制数据
        return Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, io.BytesIO):
        # 字节流对象
        return Image.open(image_input)
    else:
        raise ValueError(f"不支持的输入类型: {type(image_input)}")

def _prepare_image_for_hash(img, target_size=(64, 64), mode='RGB'):
    """准备图像用于哈希计算
    
    参数:
        img: PIL图像对象
        target_size: 目标尺寸
        mode: 目标颜色模式
    
    返回:
        PIL.Image: 处理后的图像
    """
    # 转换为指定模式
    if img.mode != mode:
        img = img.convert(mode)
    
    # 调整到目标尺寸
    img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
    return img_resized

def calculate_image_hash(image_input):
    """计算图像内容的哈希值（基于像素数据）"""
    try:
        img = _load_image_from_input(image_input)
        img_processed = _prepare_image_for_hash(img, target_size=(64, 64), mode='RGB')
        
        # 将图像转换为字节数据
        img_bytes = io.BytesIO()
        img_processed.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        # 计算哈希
        hash_sha256 = hashlib.sha256(img_data)
        return hash_sha256.hexdigest()
        
    except Exception as e:
        print(f"计算图像哈希失败: {e}")
        return None

def calculate_image_perceptual_hash(image_input):
    """计算图像感知哈希（更精确的相似图像检测）"""
    try:
        img = _load_image_from_input(image_input)
        img_processed = _prepare_image_for_hash(img, target_size=(8, 8), mode='L')
        
        # 计算平均像素值
        pixels = list(img_processed.getdata())
        avg_pixel = sum(pixels) / len(pixels)
        
        # 生成哈希：大于平均值的为1，小于的为0
        hash_bits = []
        for pixel in pixels:
            hash_bits.append('1' if pixel > avg_pixel else '0')
        
        # 转换为十六进制
        hash_string = ''.join(hash_bits)
        hash_int = int(hash_string, 2)
        return f"{hash_int:016x}"
        
    except Exception as e:
        print(f"计算感知哈希失败: {e}")
        return None

def calculate_image_hashes(image_input):
    """计算图像的所有哈希值
    
    参数:
        image_input: 可以是以下类型之一：
            - str: 文件路径
            - PIL.Image: PIL图像对象
            - bytes: 图像二进制数据
            - io.BytesIO: 字节流对象
    
    返回:
        dict: 包含所有哈希值的字典
    """
    try:
        # 计算图像内容哈希
        image_hash = calculate_image_hash(image_input)
        
        # 计算感知哈希
        perceptual_hash = calculate_image_perceptual_hash(image_input)
        
        return {
            'image_hash': image_hash,
            'perceptual_hash': perceptual_hash,
            'success': image_hash is not None and perceptual_hash is not None
        }
    except Exception as e:
        print(f"计算图像哈希失败: {e}")
        return {
            'image_hash': None,
            'perceptual_hash': None,
            'success': False
        }

def get_file_info(file_path):
    """获取文件信息"""
    try:
        stat = os.stat(file_path)
        
        # 检测 MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            # 如果无法通过扩展名检测，尝试读取文件头
            mime_type = detect_mime_type_by_content(file_path)
        
        return {
            'file_size': stat.st_size,
            'mime_type': mime_type
        }
    except Exception as e:
        print(f"获取文件信息失败: {e}")
        return {'file_size': None, 'mime_type': None}

def detect_mime_type_by_content(file_path):
    """通过文件内容检测MIME类型"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(32)  # 读取前32字节
        
        # 常见图片格式的文件头检测
        if header.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif header.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return 'image/gif'
        elif header.startswith(b'RIFF') and b'WEBP' in header[:12]:
            return 'image/webp'
        elif header.startswith(b'BM'):
            return 'image/bmp'
        elif header.startswith(b'\x00\x00\x01\x00'):
            return 'image/x-icon'
        else:
            return 'application/octet-stream'  # 未知类型
    except:
        return None

def calculate_hamming_distance(hash1, hash2):
    """计算两个感知哈希的汉明距离"""
    if len(hash1) != len(hash2):
        return float('inf')
    
    distance = 0
    for i in range(len(hash1)):
        if hash1[i] != hash2[i]:
            distance += 1
    
    return distance

def get_image_dimensions(image_input):
    """获取图像尺寸信息"""
    try:
        img = _load_image_from_input(image_input)
        return {
            'width': img.width,
            'height': img.height,
            'mode': img.mode,
            'format': img.format
        }
    except Exception as e:
        print(f"获取图像尺寸失败: {e}")
        return None

def resize_image(image_input, target_size=(64, 64), mode='RGB'):
    """调整图像大小和模式"""
    try:
        img = _load_image_from_input(image_input)
        img_resized = _prepare_image_for_hash(img, target_size=target_size, mode=mode)
        return img_resized
    except Exception as e:
        print(f"调整图像大小失败: {e}")
        return None

def convert_image_to_bytes(image_input, format='PNG'):
    """将图像转换为字节数据"""
    try:
        img = _load_image_from_input(image_input)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=format)
        return img_bytes.getvalue()
    except Exception as e:
        print(f"转换图像为字节失败: {e}")
        return None
