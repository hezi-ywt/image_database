#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片服务类 - 标准服务设计
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from .images import Images
from .metadata import Images_metadata
from .caption import ImageCaption


class ImagesService:
    """图片数据服务类 - 标准服务设计"""
    
    def __init__(self, session: Session):
        """初始化服务
        Args:
            session: 数据库会话（必须传入）
        """
        self.session = session
    
    def create_image(self, file_path: str, description: Optional[str] = None) -> Images:
        """创建图片记录
        
        Args:
            file_path: 图片文件路径
            description: 图片描述
            
        Returns:
            Images: 创建的图片对象
        """
        try:
            image = Images(
                file_path=file_path,
                description=description
            )
            self.session.add(image)
            self.session.flush()  # 获取ID但不提交
            return image
        except Exception as e:
            raise Exception(f"创建图片记录失败: {str(e)}")
    
    def get_by_id(self, image_id: int) -> Optional[Images]:
        """根据ID获取图片
        
        Args:
            image_id: 图片ID
            
        Returns:
            Images: 图片对象，如果不存在返回None
        """
        return self.session.query(Images).filter(
            Images.id == image_id,
            Images.deleted_at.is_(None)
        ).first()
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Images]:
        """获取所有图片
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[Images]: 图片列表
        """
        query = self.session.query(Images).filter(Images.deleted_at.is_(None))
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def update_image(self, image_id: int, **updates) -> Optional[Images]:
        """更新图片
        
        Args:
            image_id: 图片ID
            **updates: 要更新的字段
            
        Returns:
            Images: 更新后的图片对象，如果不存在返回None
        """
        image = self.get_by_id(image_id)
        if not image:
            return None
        
        for key, value in updates.items():
            if hasattr(image, key):
                setattr(image, key, value)
        
        image.updated_at = datetime.now()
        return image
    
    def soft_delete(self, image_id: int) -> bool:
        """软删除图片
        
        Args:
            image_id: 图片ID
            
        Returns:
            bool: 是否删除成功
        """
        image = self.get_by_id(image_id)
        if not image:
            return False
        
        image.deleted_at = datetime.now()
        return True
    
    def hard_delete(self, image_id: int) -> bool:
        """硬删除图片
        
        Args:
            image_id: 图片ID
            
        Returns:
            bool: 是否删除成功
        """
        image = self.get_by_id(image_id)
        if not image:
            return False
        
        # 删除关联的metadata
        if image.image_metadata:
            self.session.delete(image.image_metadata)
        
        # 删除关联的captions
        captions = self.session.query(ImageCaption).filter(ImageCaption.image_id == image_id).all()
        for caption in captions:
            self.session.delete(caption)
        
        self.session.delete(image)
        return True
    
    def count(self) -> int:
        """统计图片数量
        
        Returns:
            int: 图片数量
        """
        return self.session.query(Images).filter(Images.deleted_at.is_(None)).count()
    
    def search_by_description(self, keyword: str) -> List[Images]:
        """根据描述搜索图片
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Images]: 匹配的图片列表
        """
        return self.session.query(Images).filter(
            Images.deleted_at.is_(None),
            Images.description.contains(keyword)
        ).all()
    
    def get_recent_images(self, limit: int = 10) -> List[Images]:
        """获取最近的图片
        
        Args:
            limit: 限制数量
            
        Returns:
            List[Images]: 最近的图片列表
        """
        return self.session.query(Images).filter(
            Images.deleted_at.is_(None)
        ).order_by(Images.created_at.desc()).limit(limit).all()
