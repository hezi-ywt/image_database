from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, and_, or_
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional, Dict, Any
from .base import Base, BaseMixin


# 定义 Images 模型
class Images(Base, BaseMixin):
    __tablename__ = 'images'
    
    file_path = Column(String(500), nullable=False)
    description = Column(Text)
    
    # 关系定义 - 一个图像对应一个元数据
    image_metadata = relationship("Images_metadata", back_populates="image", uselist=False)
    
    def __repr__(self):
        return f"<Images(id={self.id}, file_path='{self.file_path}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'metadata': self.image_metadata.to_dict() if self.image_metadata else None
        }