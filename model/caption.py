from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum as PyEnum
from .base import Base, BaseMixin


class LanguageCode(PyEnum):
    """支持的语言代码枚举"""
    ZH = "zh"      # 中文
    EN = "en"      # 英文
    JA = "ja"      # 日文
    KO = "ko"      # 韩文
    FR = "fr"      # 法文
    DE = "de"      # 德文
    ES = "es"      # 西班牙文
    IT = "it"      # 意大利文
    RU = "ru"      # 俄文
    AR = "ar"      # 阿拉伯文


class CaptionType(Base, BaseMixin):
    """Caption类型表 - 存储caption的分类/标签类型"""
    __tablename__ = 'caption_types'
    
    name = Column(String(100), nullable=False, unique=True, index=True)  # caption类型名称，如"description", "tags", "keywords"
    display_name = Column(String(100))  # 显示名称，如"描述", "标签", "关键词"
    description = Column(Text)  # 类型说明
    is_active = Column(Boolean, default=True)  # 是否启用
    
    # 关系定义
    captions = relationship("ImageCaption", back_populates="caption_type")
    
    def __repr__(self):
        return f"<CaptionType(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class ImageCaption(Base, BaseMixin):
    """图片Caption表 - 存储具体的caption内容"""
    __tablename__ = 'image_captions'
    
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    caption_type_id = Column(Integer, ForeignKey('caption_types.id'), nullable=False) 
    content = Column(Text, nullable=False)  # caption内容
    confidence = Column(Float)  # 置信度（如果是AI生成的）
    language = Column(Enum(LanguageCode), default=LanguageCode.EN)  # 语言代码
    is_primary = Column(Boolean, default=False)  # 是否为主要caption
    
    # 关系定义
    image = relationship("Images", back_populates="captions")
    caption_type = relationship("CaptionType", back_populates="captions")
    
    def __repr__(self):
        return f"<ImageCaption(id={self.id}, image_id={self.image_id}, type='{self.caption_type.name if self.caption_type else 'Unknown'}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'caption_type_id': self.caption_type_id,
            'content': self.content,
            'confidence': self.confidence,
            'language': self.language,
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'caption_type': self.caption_type.to_dict() if self.caption_type else None
        }

