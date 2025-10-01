#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图集数据库模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from .base import Base, BaseMixin


class GalleryType(PyEnum):
    """图集类型枚举"""
    STYLE = "style"      # 风格图集
    CHARACTER = "character"      # 角色图集
    CONCEPT = "concept"      # 概念图集
    COLLECTION = "collection"      # 普通图集
    SERIES = "series"              # 系列图集
    ALBUM = "album"                # 相册
    PROJECT = "project"            # 项目
    OTHER = "other"                # 其他


class Gallery(Base, BaseMixin):
    """图集模型"""
    __tablename__ = "galleries"
    
    # 基本信息
    name = Column(String(255), nullable=False, comment="图集名称")
    description = Column(Text, comment="图集描述")
    gallery_type = Column(Enum(GalleryType), default=GalleryType.COLLECTION, comment="图集类型")
    
    # 层级关系
    parent_id = Column(Integer, ForeignKey("galleries.id"), nullable=True, comment="父图集ID")
    level = Column(Integer, default=0, comment="层级深度")
    path = Column(String(1000), comment="图集路径，如：/根图集/子图集")
    
    # 统计信息
    image_count = Column(Integer, default=0, comment="图片数量")
    sub_gallery_count = Column(Integer, default=0, comment="子图集数量")
    total_image_count = Column(Integer, default=0, comment="总图片数量（包含子图集）")
    
    # 显示设置
    cover_image_id = Column(Integer, ForeignKey("images.id"), nullable=True, comment="封面图片ID")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_public = Column(Boolean, default=True, comment="是否公开")
    
    # 关系定义
    parent = relationship("Gallery", remote_side="Gallery.id", back_populates="children")
    children = relationship("Gallery", back_populates="parent", cascade="all, delete-orphan")
    images = relationship("GalleryImage", back_populates="gallery", cascade="all, delete-orphan")
    cover_image = relationship("Images", foreign_keys=[cover_image_id])
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'gallery_type': self.gallery_type.value if self.gallery_type else None,
            'parent_id': self.parent_id,
            'level': self.level,
            'path': self.path,
            'image_count': self.image_count,
            'sub_gallery_count': self.sub_gallery_count,
            'total_image_count': self.total_image_count,
            'cover_image_id': self.cover_image_id,
            'sort_order': self.sort_order,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
    
    def get_full_path(self):
        """获取完整路径"""
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.name}"
        return self.name
    
    def get_ancestors(self):
        """获取所有祖先图集"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors[::-1]  # 反转，从根到父
    
    def get_descendants(self):
        """获取所有后代图集"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class GalleryImage(Base, BaseMixin):
    """图集图片关联模型"""
    __tablename__ = "gallery_images"
    
    # 关联信息
    gallery_id = Column(Integer, ForeignKey("galleries.id"), nullable=False, comment="图集ID")
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False, comment="图片ID")
    
    # 显示设置
    sort_order = Column(Integer, default=0, comment="在图集中的排序")
    is_cover = Column(Boolean, default=False, comment="是否为封面图片")
    is_featured = Column(Boolean, default=False, comment="是否为精选图片")
    
    # 关系定义
    gallery = relationship("Gallery", back_populates="images")
    image = relationship("Images")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'gallery_id': self.gallery_id,
            'image_id': self.image_id,
            'sort_order': self.sort_order,
            'is_cover': self.is_cover,
            'is_featured': self.is_featured,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class GalleryTag(Base, BaseMixin):
    """图集标签模型"""
    __tablename__ = "gallery_tags"
    
    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="标签名称")
    description = Column(Text, comment="标签描述")
    
    # 关系定义
    galleries = relationship("GalleryTagAssociation", back_populates="tag")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }


class GalleryTagAssociation(Base, BaseMixin):
    """图集标签关联模型"""
    __tablename__ = "gallery_tag_associations"
    
    # 关联信息
    gallery_id = Column(Integer, ForeignKey("galleries.id"), nullable=False, comment="图集ID")
    tag_id = Column(Integer, ForeignKey("gallery_tags.id"), nullable=False, comment="标签ID")
    
    # 关系定义
    gallery = relationship("Gallery")
    tag = relationship("GalleryTag", back_populates="galleries")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'gallery_id': self.gallery_id,
            'tag_id': self.tag_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
