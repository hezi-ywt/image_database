#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Caption服务类 - 标准服务设计
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict
from .caption import CaptionType, ImageCaption, LanguageCode


class CaptionService:
    """Caption服务类 - 标准服务设计"""
    
    def __init__(self, session: Session):
        """初始化服务
        Args:
            session: 数据库会话（必须传入）
        """
        self.session = session
    
    def get_or_create_caption_type(self, name: str, description: str = None) -> CaptionType:
        """获取或创建caption类型
        
        Args:
            name: caption类型名称
            description: 描述
            
        Returns:
            CaptionType: caption类型对象
        """
        caption_type = self.session.query(CaptionType).filter(
            CaptionType.name == name,
            CaptionType.deleted_at.is_(None)
        ).first()
        
        if not caption_type:
            caption_type = CaptionType(
                name=name,
                description=description or f"Caption类型: {name}"
            )
            self.session.add(caption_type)
            self.session.flush()
        
        return caption_type
    
    def add_caption(self, image_id: int, caption_type_name: str, content: str, 
                   confidence: float = None, language: LanguageCode = LanguageCode.EN, 
                   is_primary: bool = False) -> ImageCaption:
        """添加caption
        
        Args:
            image_id: 图片ID
            caption_type_name: caption类型名称
            content: caption内容
            confidence: 置信度
            language: 语言代码
            is_primary: 是否为主要caption
            
        Returns:
            ImageCaption: 创建的caption对象
        """
        try:
            # 获取或创建caption类型
            caption_type = self.get_or_create_caption_type(caption_type_name)
            
            # 创建caption
            caption = ImageCaption(
                image_id=image_id,
                caption_type_id=caption_type.id,
                content=content,
                confidence=confidence,
                language=language,
                is_primary=is_primary
            )
            self.session.add(caption)
            self.session.flush()
            return caption
        except Exception as e:
            raise Exception(f"添加caption失败: {str(e)}")
    
    def get_image_captions(self, image_id: int, caption_type_name: str = None) -> List[ImageCaption]:
        """获取图片的captions
        
        Args:
            image_id: 图片ID
            caption_type_name: caption类型名称（可选）
            
        Returns:
            List[ImageCaption]: caption列表
        """
        query = self.session.query(ImageCaption).filter(
            ImageCaption.image_id == image_id,
            ImageCaption.deleted_at.is_(None)
        )
        
        if caption_type_name:
            caption_type = self.get_or_create_caption_type(caption_type_name)
            if caption_type:
                query = query.filter(ImageCaption.caption_type_id == caption_type.id)
        
        return query.all()
    
    def get_image_captions_by_type(self, image_id: int) -> Dict[str, List[ImageCaption]]:
        """按类型分组获取图片的captions
        
        Args:
            image_id: 图片ID
            
        Returns:
            Dict[str, List[ImageCaption]]: 按类型分组的captions
        """
        captions = self.get_image_captions(image_id)
        result = {}
        
        for caption in captions:
            type_name = caption.caption_type.name
            if type_name not in result:
                result[type_name] = []
            result[type_name].append(caption)
        
        return result
    
    def get_primary_caption(self, image_id: int, caption_type_name: str = None) -> Optional[ImageCaption]:
        """获取主要caption
        
        Args:
            image_id: 图片ID
            caption_type_name: caption类型名称（可选）
            
        Returns:
            ImageCaption: 主要caption，如果不存在返回None
        """
        query = self.session.query(ImageCaption).filter(
            ImageCaption.image_id == image_id,
            ImageCaption.is_primary == True,
            ImageCaption.deleted_at.is_(None)
        )
        
        if caption_type_name:
            caption_type = self.get_or_create_caption_type(caption_type_name)
            if caption_type:
                query = query.filter(ImageCaption.caption_type_id == caption_type.id)
        
        return query.first()
    
    def update_caption(self, caption_id: int, content: str = None, confidence: float = None, 
                      is_primary: bool = None) -> Optional[ImageCaption]:
        """更新caption
        
        Args:
            caption_id: caption ID
            content: 新内容
            confidence: 新置信度
            is_primary: 是否为主要caption
            
        Returns:
            ImageCaption: 更新后的caption对象，如果不存在返回None
        """
        caption = self.session.query(ImageCaption).filter(
            ImageCaption.id == caption_id,
            ImageCaption.deleted_at.is_(None)
        ).first()
        
        if not caption:
            return None
        
        if content is not None:
            caption.content = content
        if confidence is not None:
            caption.confidence = confidence
        if is_primary is not None:
            caption.is_primary = is_primary
        
        caption.updated_at = datetime.now()
        return caption
    
    def delete_caption(self, caption_id: int, hard_delete: bool = False) -> bool:
        """删除caption
        
        Args:
            caption_id: caption ID
            hard_delete: 是否硬删除
            
        Returns:
            bool: 是否删除成功
        """
        caption = self.session.query(ImageCaption).filter(
            ImageCaption.id == caption_id,
            ImageCaption.deleted_at.is_(None)
        ).first()
        
        if not caption:
            return False
        
        if hard_delete:
            self.session.delete(caption)
        else:
            caption.deleted_at = datetime.now()
        
        return True
    
    def batch_add_captions(self, image_id: int, captions_data: List[Dict]) -> List[ImageCaption]:
        """批量添加captions
        
        Args:
            image_id: 图片ID
            captions_data: caption数据列表
            
        Returns:
            List[ImageCaption]: 创建的caption列表
        """
        captions = []
        for data in captions_data:
            caption = self.add_caption(
                image_id=image_id,
                caption_type_name=data.get('type', 'description'),
                content=data.get('content', ''),
                confidence=data.get('confidence'),
                language=data.get('language', LanguageCode.EN),
                is_primary=data.get('is_primary', False)
            )
            captions.append(caption)
        
        return captions
    
    def get_caption_types(self) -> List[CaptionType]:
        """获取所有caption类型
        
        Returns:
            List[CaptionType]: caption类型列表
        """
        return self.session.query(CaptionType).filter(
            CaptionType.deleted_at.is_(None)
        ).all()
    
    def search_captions(self, keyword: str, caption_type_name: str = None) -> List[ImageCaption]:
        """搜索captions
        
        Args:
            keyword: 搜索关键词
            caption_type_name: caption类型名称（可选）
            
        Returns:
            List[ImageCaption]: 匹配的caption列表
        """
        query = self.session.query(ImageCaption).filter(
            ImageCaption.content.contains(keyword),
            ImageCaption.deleted_at.is_(None)
        )
        
        if caption_type_name:
            caption_type = self.get_or_create_caption_type(caption_type_name)
            if caption_type:
                query = query.filter(ImageCaption.caption_type_id == caption_type.id)
        
        return query.all()