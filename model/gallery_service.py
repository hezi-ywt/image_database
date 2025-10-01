#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图集服务类 - 标准服务设计
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime
from typing import List, Optional, Dict, Any
from .gallery import Gallery, GalleryImage, GalleryTag, GalleryTagAssociation, GalleryType


class GalleryService:
    """图集服务类 - 标准服务设计"""
    
    def __init__(self, session: Session):
        """初始化服务
        Args:
            session: 数据库会话（必须传入）
        """
        self.session = session
    
    # ========== 图集管理 ==========
    
    def create_gallery(self, name: str, description: str = None, gallery_type: GalleryType = GalleryType.COLLECTION,
                      parent_id: int = None, is_public: bool = True) -> Gallery:
        """创建图集
        
        Args:
            name: 图集名称
            description: 图集描述
            gallery_type: 图集类型
            parent_id: 父图集ID
            is_public: 是否公开
            
        Returns:
            Gallery: 创建的图集对象
        """
        try:
            # 计算层级和路径
            level = 0
            path = name
            if parent_id:
                parent = self.get_gallery_by_id(parent_id)
                if parent:
                    level = parent.level + 1
                    path = f"{parent.path}/{name}"
            
            gallery = Gallery(
                name=name,
                description=description,
                gallery_type=gallery_type,
                parent_id=parent_id,
                level=level,
                path=path,
                is_public=is_public
            )
            self.session.add(gallery)
            self.session.flush()
            
            # 更新父图集的子图集数量
            if parent_id:
                self._update_parent_counts(parent_id)
            
            return gallery
        except Exception as e:
            raise Exception(f"创建图集失败: {str(e)}")
    
    def get_gallery_by_id(self, gallery_id: int) -> Optional[Gallery]:
        """根据ID获取图集
        
        Args:
            gallery_id: 图集ID
            
        Returns:
            Gallery: 图集对象，如果不存在返回None
        """
        return self.session.query(Gallery).filter(
            Gallery.id == gallery_id,
            Gallery.deleted_at.is_(None)
        ).first()
    
    def get_galleries_by_parent(self, parent_id: int = None) -> List[Gallery]:
        """获取指定父图集的子图集
        
        Args:
            parent_id: 父图集ID，None表示根图集
            
        Returns:
            List[Gallery]: 子图集列表
        """
        return self.session.query(Gallery).filter(
            Gallery.parent_id == parent_id,
            Gallery.deleted_at.is_(None)
        ).order_by(Gallery.sort_order, Gallery.created_at).all()
    
    def get_gallery_tree(self, root_id: int = None) -> Dict[str, Any]:
        """获取图集树结构
        
        Args:
            root_id: 根图集ID，None表示从所有根图集开始
            
        Returns:
            Dict: 图集树结构
        """
        def build_tree(gallery_id):
            gallery = self.get_gallery_by_id(gallery_id)
            if not gallery:
                return None
            
            children = self.get_galleries_by_parent(gallery_id)
            tree = {
                'gallery': gallery.to_dict(),
                'children': []
            }
            
            for child in children:
                child_tree = build_tree(child.id)
                if child_tree:
                    tree['children'].append(child_tree)
            
            return tree
        
        if root_id:
            return build_tree(root_id)
        else:
            # 获取所有根图集
            root_galleries = self.get_galleries_by_parent(None)
            return {
                'galleries': [build_tree(gallery.id) for gallery in root_galleries]
            }
    
    def update_gallery(self, gallery_id: int, **updates) -> Optional[Gallery]:
        """更新图集
        
        Args:
            gallery_id: 图集ID
            **updates: 要更新的字段
            
        Returns:
            Gallery: 更新后的图集对象，如果不存在返回None
        """
        gallery = self.get_gallery_by_id(gallery_id)
        if not gallery:
            return None
        
        for key, value in updates.items():
            if hasattr(gallery, key):
                setattr(gallery, key, value)
        
        gallery.updated_at = datetime.now()
        return gallery
    
    def move_gallery(self, gallery_id: int, new_parent_id: int = None) -> bool:
        """移动图集到新的父图集
        
        Args:
            gallery_id: 要移动的图集ID
            new_parent_id: 新的父图集ID，None表示移动到根级别
            
        Returns:
            bool: 是否移动成功
        """
        gallery = self.get_gallery_by_id(gallery_id)
        if not gallery:
            return False
        
        # 检查是否会造成循环引用
        if new_parent_id:
            new_parent = self.get_gallery_by_id(new_parent_id)
            if new_parent and self._is_descendant(new_parent, gallery):
                raise Exception("不能将图集移动到其子图集中")
        
        old_parent_id = gallery.parent_id
        gallery.parent_id = new_parent_id
        
        # 更新路径和层级
        self._update_gallery_path(gallery)
        
        # 更新统计信息
        if old_parent_id:
            self._update_parent_counts(old_parent_id)
        if new_parent_id:
            self._update_parent_counts(new_parent_id)
        
        return True
    
    def delete_gallery(self, gallery_id: int, hard_delete: bool = False) -> bool:
        """删除图集
        
        Args:
            gallery_id: 图集ID
            hard_delete: 是否硬删除
            
        Returns:
            bool: 是否删除成功
        """
        gallery = self.get_gallery_by_id(gallery_id)
        if not gallery:
            return False
        
        if hard_delete:
            # 硬删除：删除所有子图集和关联
            self._hard_delete_gallery(gallery)
        else:
            # 软删除
            gallery.deleted_at = datetime.now()
            # 递归软删除所有子图集
            self._soft_delete_children(gallery_id)
        
        # 更新父图集统计
        if gallery.parent_id:
            self._update_parent_counts(gallery.parent_id)
        
        return True
    
    # ========== 图片管理 ==========
    
    def add_image_to_gallery(self, gallery_id: int, image_id: int, 
                            sort_order: int = 0, is_cover: bool = False,
                            is_featured: bool = False) -> GalleryImage:
        """将图片添加到图集
        
        Args:
            gallery_id: 图集ID
            image_id: 图片ID
            sort_order: 排序顺序
            is_cover: 是否为封面
            is_featured: 是否为精选
            
        Returns:
            GalleryImage: 关联对象
        """
        try:
            # 检查是否已存在
            existing = self.session.query(GalleryImage).filter(
                GalleryImage.gallery_id == gallery_id,
                GalleryImage.image_id == image_id,
                GalleryImage.deleted_at.is_(None)
            ).first()
            
            if existing:
                return existing
            
            gallery_image = GalleryImage(
                gallery_id=gallery_id,
                image_id=image_id,
                sort_order=sort_order,
                is_cover=is_cover,
                is_featured=is_featured
            )
            self.session.add(gallery_image)
            self.session.flush()
            
            # 更新图集统计
            self._update_gallery_counts(gallery_id)
            
            return gallery_image
        except Exception as e:
            raise Exception(f"添加图片到图集失败: {str(e)}")
    
    def remove_image_from_gallery(self, gallery_id: int, image_id: int, 
                                 hard_delete: bool = False) -> bool:
        """从图集中移除图片
        
        Args:
            gallery_id: 图集ID
            image_id: 图片ID
            hard_delete: 是否硬删除
            
        Returns:
            bool: 是否移除成功
        """
        gallery_image = self.session.query(GalleryImage).filter(
            GalleryImage.gallery_id == gallery_id,
            GalleryImage.image_id == image_id,
            GalleryImage.deleted_at.is_(None)
        ).first()
        
        if not gallery_image:
            return False
        
        if hard_delete:
            self.session.delete(gallery_image)
        else:
            gallery_image.deleted_at = datetime.now()
        
        # 更新图集统计
        self._update_gallery_counts(gallery_id)
        
        return True
    
    def get_gallery_images(self, gallery_id: int, include_subgalleries: bool = False) -> List[GalleryImage]:
        """获取图集中的图片
        
        Args:
            gallery_id: 图集ID
            include_subgalleries: 是否包含子图集的图片
            
        Returns:
            List[GalleryImage]: 图片关联列表
        """
        if include_subgalleries:
            # 获取所有子图集ID
            sub_gallery_ids = [gallery_id]
            sub_galleries = self.get_galleries_by_parent(gallery_id)
            for sub_gallery in sub_galleries:
                sub_gallery_ids.extend(self._get_all_descendant_ids(sub_gallery.id))
            
            return self.session.query(GalleryImage).filter(
                GalleryImage.gallery_id.in_(sub_gallery_ids),
                GalleryImage.deleted_at.is_(None)
            ).order_by(GalleryImage.sort_order, GalleryImage.created_at).all()
        else:
            return self.session.query(GalleryImage).filter(
                GalleryImage.gallery_id == gallery_id,
                GalleryImage.deleted_at.is_(None)
            ).order_by(GalleryImage.sort_order, GalleryImage.created_at).all()
    
    def set_cover_image(self, gallery_id: int, image_id: int) -> bool:
        """设置图集封面图片
        
        Args:
            gallery_id: 图集ID
            image_id: 图片ID
            
        Returns:
            bool: 是否设置成功
        """
        # 清除其他封面
        self.session.query(GalleryImage).filter(
            GalleryImage.gallery_id == gallery_id,
            GalleryImage.is_cover == True,
            GalleryImage.deleted_at.is_(None)
        ).update({"is_cover": False})
        
        # 设置新封面
        gallery_image = self.session.query(GalleryImage).filter(
            GalleryImage.gallery_id == gallery_id,
            GalleryImage.image_id == image_id,
            GalleryImage.deleted_at.is_(None)
        ).first()
        
        if gallery_image:
            gallery_image.is_cover = True
            # 更新图集的封面图片ID
            gallery = self.get_gallery_by_id(gallery_id)
            if gallery:
                gallery.cover_image_id = image_id
            return True
        
        return False
    
    # ========== 标签管理 ==========
    
    def create_tag(self, name: str, description: str = None) -> GalleryTag:
        """创建标签
        
        Args:
            name: 标签名称
            description: 标签描述
            
        Returns:
            GalleryTag: 创建的标签对象
        """
        try:
            tag = GalleryTag(
                name=name,
                description=description
            )
            self.session.add(tag)
            self.session.flush()
            return tag
        except Exception as e:
            raise Exception(f"创建标签失败: {str(e)}")
    
    def add_tag_to_gallery(self, gallery_id: int, tag_id: int) -> bool:
        """为图集添加标签
        
        Args:
            gallery_id: 图集ID
            tag_id: 标签ID
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 检查是否已存在
            existing = self.session.query(GalleryTagAssociation).filter(
                GalleryTagAssociation.gallery_id == gallery_id,
                GalleryTagAssociation.tag_id == tag_id,
                GalleryTagAssociation.deleted_at.is_(None)
            ).first()
            
            if existing:
                return True
            
            association = GalleryTagAssociation(
                gallery_id=gallery_id,
                tag_id=tag_id
            )
            self.session.add(association)
            return True
        except Exception as e:
            raise Exception(f"添加标签失败: {str(e)}")
    
    def remove_tag_from_gallery(self, gallery_id: int, tag_id: int) -> bool:
        """从图集移除标签
        
        Args:
            gallery_id: 图集ID
            tag_id: 标签ID
            
        Returns:
            bool: 是否移除成功
        """
        association = self.session.query(GalleryTagAssociation).filter(
            GalleryTagAssociation.gallery_id == gallery_id,
            GalleryTagAssociation.tag_id == tag_id,
            GalleryTagAssociation.deleted_at.is_(None)
        ).first()
        
        if association:
            association.deleted_at = datetime.now()
            return True
        
        return False
    
    def get_gallery_tags(self, gallery_id: int) -> List[GalleryTag]:
        """获取图集的标签
        
        Args:
            gallery_id: 图集ID
            
        Returns:
            List[GalleryTag]: 标签列表
        """
        return self.session.query(GalleryTag).join(GalleryTagAssociation).filter(
            GalleryTagAssociation.gallery_id == gallery_id,
            GalleryTagAssociation.deleted_at.is_(None),
            GalleryTag.deleted_at.is_(None)
        ).all()
    
    # ========== 搜索和统计 ==========
    
    def search_galleries(self, keyword: str, gallery_type: GalleryType = None) -> List[Gallery]:
        """搜索图集
        
        Args:
            keyword: 搜索关键词
            gallery_type: 图集类型过滤
            
        Returns:
            List[Gallery]: 匹配的图集列表
        """
        query = self.session.query(Gallery).filter(
            Gallery.deleted_at.is_(None),
            or_(
                Gallery.name.contains(keyword),
                Gallery.description.contains(keyword)
            )
        )
        
        if gallery_type:
            query = query.filter(Gallery.gallery_type == gallery_type)
        
        return query.order_by(Gallery.created_at.desc()).all()
    
    def get_gallery_statistics(self, gallery_id: int) -> Dict[str, Any]:
        """获取图集统计信息
        
        Args:
            gallery_id: 图集ID
            
        Returns:
            Dict: 统计信息
        """
        gallery = self.get_gallery_by_id(gallery_id)
        if not gallery:
            return {}
        
        # 获取直接图片数量
        direct_images = self.get_gallery_images(gallery_id, include_subgalleries=False)
        
        # 获取所有子图集
        descendants = self._get_all_descendant_ids(gallery_id)
        
        # 获取总图片数量
        total_images = self.session.query(GalleryImage).filter(
            GalleryImage.gallery_id.in_([gallery_id] + descendants),
            GalleryImage.deleted_at.is_(None)
        ).count()
        
        return {
            'gallery_id': gallery_id,
            'name': gallery.name,
            'direct_image_count': len(direct_images),
            'sub_gallery_count': len(descendants),
            'total_image_count': total_images,
            'level': gallery.level,
            'path': gallery.path
        }
    
    # ========== 私有方法 ==========
    
    def _update_gallery_path(self, gallery: Gallery):
        """更新图集路径"""
        if gallery.parent:
            gallery.path = f"{gallery.parent.path}/{gallery.name}"
            gallery.level = gallery.parent.level + 1
        else:
            gallery.path = gallery.name
            gallery.level = 0
        
        # 递归更新所有子图集
        for child in gallery.children:
            self._update_gallery_path(child)
    
    def _update_parent_counts(self, parent_id: int):
        """更新父图集统计"""
        parent = self.get_gallery_by_id(parent_id)
        if parent:
            # 更新子图集数量
            parent.sub_gallery_count = self.session.query(Gallery).filter(
                Gallery.parent_id == parent_id,
                Gallery.deleted_at.is_(None)
            ).count()
            
            # 更新总图片数量
            descendants = self._get_all_descendant_ids(parent_id)
            parent.total_image_count = self.session.query(GalleryImage).filter(
                GalleryImage.gallery_id.in_([parent_id] + descendants),
                GalleryImage.deleted_at.is_(None)
            ).count()
    
    def _update_gallery_counts(self, gallery_id: int):
        """更新图集统计"""
        gallery = self.get_gallery_by_id(gallery_id)
        if gallery:
            gallery.image_count = self.session.query(GalleryImage).filter(
                GalleryImage.gallery_id == gallery_id,
                GalleryImage.deleted_at.is_(None)
            ).count()
    
    def _get_all_descendant_ids(self, gallery_id: int) -> List[int]:
        """获取所有后代图集ID"""
        descendants = []
        children = self.get_galleries_by_parent(gallery_id)
        for child in children:
            descendants.append(child.id)
            descendants.extend(self._get_all_descendant_ids(child.id))
        return descendants
    
    def _is_descendant(self, ancestor: Gallery, descendant: Gallery) -> bool:
        """检查是否为后代关系"""
        current = descendant.parent
        while current:
            if current.id == ancestor.id:
                return True
            current = current.parent
        return False
    
    def _soft_delete_children(self, gallery_id: int):
        """递归软删除子图集"""
        children = self.get_galleries_by_parent(gallery_id)
        for child in children:
            child.deleted_at = datetime.now()
            self._soft_delete_children(child.id)
    
    def _hard_delete_gallery(self, gallery: Gallery):
        """硬删除图集及其所有关联"""
        # 删除所有子图集
        for child in gallery.children:
            self._hard_delete_gallery(child)
        
        # 删除图片关联
        self.session.query(GalleryImage).filter(
            GalleryImage.gallery_id == gallery.id
        ).delete()
        
        # 删除标签关联
        self.session.query(GalleryTagAssociation).filter(
            GalleryTagAssociation.gallery_id == gallery.id
        ).delete()
        
        # 删除图集
        self.session.delete(gallery)
