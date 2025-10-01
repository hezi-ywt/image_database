from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, BaseMixin
from .image_util import calculate_image_hashes, get_file_info

class Images_metadata(Base, BaseMixin):
    __tablename__ = 'images_metadata'
    
    # 外键关联到 Images 表
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False, unique=True)
    
    # 文件元数据
    file_size = Column(Integer)  # 文件大小（字节）
    mime_type = Column(String(100))  # 文件类型
    
    # 图像内容哈希
    image_hash = Column(String(64), nullable=False, unique=True, index=True)  # 图像内容哈希
    perceptual_hash = Column(String(16), index=True)  # 感知哈希（用于相似图像检测）
    
    # 图像尺寸信息
    image_width = Column(Integer)  # 图片宽度
    image_height = Column(Integer)  # 图片高度
    
    # 图像处理信息
    color_space = Column(String(20))  # 颜色空间 (RGB, RGBA, CMYK等)
    bit_depth = Column(Integer)  # 位深度
    has_transparency = Column(Boolean, default=False)  # 是否有透明通道
    
    # 文件完整性
    file_checksum = Column(String(64))  # 文件校验和
    is_corrupted = Column(Boolean, default=False)  # 是否损坏
    
    # 关系定义
    image = relationship("Images", back_populates="image_metadata")
    
    def __repr__(self):
        return f"<Images_metadata(id={self.id}, image_id={self.image_id}, size={self.image_width}x{self.image_height})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'image_id': self.image_id,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'image_hash': self.image_hash,
            'perceptual_hash': self.perceptual_hash,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'color_space': self.color_space,
            'bit_depth': self.bit_depth,
            'has_transparency': self.has_transparency,
            'file_checksum': self.file_checksum,
            'is_corrupted': self.is_corrupted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
