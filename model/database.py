from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from .base import engine
from .images import Images
from .metadata import Images_metadata
from .image_util import calculate_image_hashes, get_file_info, calculate_hamming_distance

def _get_db_session():
    """获取数据库会话"""
    Session = sessionmaker(bind=engine)
    return Session()

def _with_db_session(func):
    """数据库会话装饰器，自动管理会话的创建和关闭"""
    def wrapper(*args, **kwargs):
        session = _get_db_session()
        try:
            return func(session, *args, **kwargs)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    return wrapper

def _determine_file_path(image_input, file_path=None):
    """确定文件路径"""
    if file_path is None:
        if isinstance(image_input, str):
            return image_input
        else:
            return f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    return file_path

def _get_file_info_for_input(image_input):
    """根据输入类型获取文件信息"""
    if isinstance(image_input, str) and os.path.exists(image_input):
        return get_file_info(image_input)
    else:
        # 对于非文件输入，设置默认值
        return {
            'file_size': None,
            'mime_type': 'image/jpeg'  # 默认类型
        }

def create_image_with_metadata(image_input, description=None, image_width=None, image_height=None, file_path=None):
    """创建图像记录及其元数据
    
    参数:
        image_input: 图像输入（文件路径、PIL图像、二进制数据等）
        description: 图像描述
        image_width: 图像宽度
        image_height: 图像高度
        file_path: 文件路径（如果image_input不是文件路径）
    """
    session = _get_db_session()
    
    try:
        # 确定文件路径
        file_path = _determine_file_path(image_input, file_path)
        
        # 创建图像记录
        image = Images(
            file_path=file_path,
            description=description
        )
        session.add(image)
        session.flush()  # 获取 image.id
        
        # 计算图像哈希
        hash_result = calculate_image_hashes(image_input)
        
        # 获取文件信息
        file_info = _get_file_info_for_input(image_input)
        
        # 创建元数据记录
        metadata = Images_metadata(
            image_id=image.id,
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            image_hash=hash_result['image_hash'],
            perceptual_hash=hash_result['perceptual_hash'],
            image_width=image_width,
            image_height=image_height,
        )
        session.add(metadata)
        
        session.commit()
        return image, metadata
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

@_with_db_session
def find_duplicate_images(session):
    """查找重复的图像（基于图像哈希）"""
    try:
        # 查询所有元数据
        metadata_list = session.query(Images_metadata).all()
        
        # 按图像哈希分组
        hash_groups = {}
        for meta in metadata_list:
            if meta.image_hash in hash_groups:
                hash_groups[meta.image_hash].append(meta)
            else:
                hash_groups[meta.image_hash] = [meta]
        
        # 找出重复的图像
        duplicates = []
        for image_hash, metas in hash_groups.items():
            if len(metas) > 1:
                duplicates.append({
                    'image_hash': image_hash,
                    'count': len(metas),
                    'images': metas
                })
        
        return duplicates
        
    except Exception as e:
        print(f"查找重复图像失败: {e}")
        return []

@_with_db_session
def find_similar_images(session, threshold=5):
    """查找相似的图像（基于感知哈希）"""
    try:
        metadata_list = session.query(Images_metadata).all()
        similar_groups = []
        
        for i, meta1 in enumerate(metadata_list):
            if not meta1.perceptual_hash:
                continue
                
            similar_images = [meta1]
            
            for j, meta2 in enumerate(metadata_list[i+1:], i+1):
                if not meta2.perceptual_hash:
                    continue
                    
                # 计算汉明距离
                hamming_distance = calculate_hamming_distance(
                    meta1.perceptual_hash, 
                    meta2.perceptual_hash
                )
                
                if hamming_distance <= threshold:
                    similar_images.append(meta2)
            
            if len(similar_images) > 1:
                similar_groups.append({
                    'threshold': threshold,
                    'count': len(similar_images),
                    'images': similar_images
                })
        
        return similar_groups
        
    except Exception as e:
        print(f"查找相似图像失败: {e}")
        return []

@_with_db_session
def test_image_with_metadata(session):
    """测试图像和元数据的创建"""
    try:
        # 查询所有图像及其元数据
        images = session.query(Images).all()
        
        print("图像记录:")
        for image in images:
            print(f"  ID: {image.id}")
            print(f"  路径: {image.file_path}")
            print(f"  描述: {image.description}")
            
            if image.metadata:
                meta = image.metadata
                print(f"  元数据:")
                print(f"    图像哈希: {meta.image_hash}")
                print(f"    感知哈希: {meta.perceptual_hash}")
                print(f"    大小: {meta.file_size} 字节")
                print(f"    类型: {meta.mime_type}")
                print(f"    尺寸: {meta.image_width}x{meta.image_height}")
                print(f"    颜色空间: {meta.color_space}")
                print(f"    位深度: {meta.bit_depth}")
            print("-" * 50)
            
    except Exception as e:
        print(f"查询失败: {e}")
