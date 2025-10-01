#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图集系统
"""

from model.session_manager import session_manager
from model.gallery_service import GalleryService
from model.images_service import ImagesService
from model.caption_service import CaptionService
from model.gallery import GalleryType
from model.caption import LanguageCode
from model.base import create_tables
import time
import os


def test_gallery_creation():
    """测试图集创建"""
    print("=== 测试图集创建 ===")
    
    try:
        with session_manager.get_session() as session:
            gallery_service = GalleryService(session)
            
            # 创建根图集
            root_gallery = gallery_service.create_gallery(
                name="我的图库",
                description="个人图片收藏",
                gallery_type=GalleryType.COLLECTION
            )
            print(f"✅ 创建根图集: ID={root_gallery.id}, 名称={root_gallery.name}")
            
            # 创建子图集
            nature_gallery = gallery_service.create_gallery(
                name="自然风光",
                description="自然风景照片",
                gallery_type=GalleryType.ALBUM,
                parent_id=root_gallery.id
            )
            print(f"✅ 创建子图集: ID={nature_gallery.id}, 名称={nature_gallery.name}")
            
            # 创建孙图集
            mountain_gallery = gallery_service.create_gallery(
                name="山脉",
                description="山脉照片",
                gallery_type=GalleryType.SERIES,
                parent_id=nature_gallery.id
            )
            print(f"✅ 创建孙图集: ID={mountain_gallery.id}, 名称={mountain_gallery.name}")
            
            # 创建另一个子图集
            city_gallery = gallery_service.create_gallery(
                name="城市建筑",
                description="城市建筑照片",
                gallery_type=GalleryType.ALBUM,
                parent_id=root_gallery.id
            )
            print(f"✅ 创建子图集: ID={city_gallery.id}, 名称={city_gallery.name}")
            
            return root_gallery.id, nature_gallery.id, mountain_gallery.id, city_gallery.id
            
    except Exception as e:
        print(f"❌ 图集创建失败: {e}")
        return None, None, None, None


def test_gallery_tree():
    """测试图集树结构"""
    print("\n=== 测试图集树结构 ===")
    
    try:
        with session_manager.get_session() as session:
            gallery_service = GalleryService(session)
            
            # 获取图集树
            tree = gallery_service.get_gallery_tree()
            print("📁 图集树结构:")
            _print_tree(tree['galleries'], 0)
            
    except Exception as e:
        print(f"❌ 图集树测试失败: {e}")


def _print_tree(galleries, level):
    """打印树结构"""
    for item in galleries:
        if item:
            indent = "  " * level
            gallery = item['gallery']
            print(f"{indent}📁 {gallery['name']} (ID: {gallery['id']}, 类型: {gallery['gallery_type']})")
            if item['children']:
                _print_tree(item['children'], level + 1)


def test_gallery_images():
    """测试图集图片管理"""
    print("\n=== 测试图集图片管理 ===")
    
    try:
        with session_manager.get_session() as session:
            gallery_service = GalleryService(session)
            image_service = ImagesService(session)
            caption_service = CaptionService(session)
            
            # 创建一些测试图片
            test_images = []
            for i in range(3):
                image = image_service.create_image(f"/test/mountain_{i+1}.jpg", f"山脉照片{i+1}")
                caption_service.add_caption(
                    image_id=image.id,
                    caption_type_name="description",
                    content=f"美丽的山脉风景{i+1}",
                    language=LanguageCode.ZH
                )
                test_images.append(image)
                print(f"✅ 创建图片: ID={image.id}")
            
            # 获取山脉图集（假设ID为3）
            mountain_gallery = gallery_service.get_gallery_by_id(3)
            if mountain_gallery:
                # 添加图片到图集
                for i, image in enumerate(test_images):
                    gallery_image = gallery_service.add_image_to_gallery(
                        gallery_id=mountain_gallery.id,
                        image_id=image.id,
                        sort_order=i,
                        is_cover=(i == 0),  # 第一张作为封面
                        is_featured=(i == 1)  # 第二张作为精选
                    )
                    print(f"✅ 添加图片到图集: 图片ID={image.id}, 排序={i}")
                
                # 获取图集中的图片
                gallery_images = gallery_service.get_gallery_images(mountain_gallery.id)
                print(f"✅ 图集包含 {len(gallery_images)} 张图片")
                
                for gi in gallery_images:
                    print(f"   - 图片ID: {gi.image_id}, 排序: {gi.sort_order}, 封面: {gi.is_cover}, 精选: {gi.is_featured}")
            
    except Exception as e:
        print(f"❌ 图集图片管理测试失败: {e}")


def test_gallery_tags():
    """测试图集标签"""
    print("\n=== 测试图集标签 ===")
    
    try:
        with session_manager.get_session() as session:
            gallery_service = GalleryService(session)
            
            # 创建标签
            tags = []
            tag_names = ["风景", "山脉", "自然", "摄影"]
            for name in tag_names:
                tag = gallery_service.create_tag(
                    name=name,
                    description=f"{name}相关标签"
                )
                tags.append(tag)
                print(f"✅ 创建标签: {tag.name}")
            
            # 为图集添加标签
            mountain_gallery = gallery_service.get_gallery_by_id(3)
            if mountain_gallery:
                for tag in tags:
                    gallery_service.add_tag_to_gallery(mountain_gallery.id, tag.id)
                    print(f"✅ 为图集添加标签: {tag.name}")
                
                # 获取图集标签
                gallery_tags = gallery_service.get_gallery_tags(mountain_gallery.id)
                print(f"✅ 图集有 {len(gallery_tags)} 个标签:")
                for tag in gallery_tags:
                    print(f"   - {tag.name}: {tag.description}")
            
    except Exception as e:
        print(f"❌ 图集标签测试失败: {e}")


def test_gallery_statistics():
    """测试图集统计"""
    print("\n=== 测试图集统计 ===")
    
    try:
        with session_manager.get_session() as session:
            gallery_service = GalleryService(session)
            
            # 获取根图集统计
            root_gallery = gallery_service.get_gallery_by_id(1)
            if root_gallery:
                stats = gallery_service.get_gallery_statistics(root_gallery.id)
                print(f"📊 根图集统计:")
                print(f"   - 名称: {stats['name']}")
                print(f"   - 直接图片数: {stats['direct_image_count']}")
                print(f"   - 子图集数: {stats['sub_gallery_count']}")
                print(f"   - 总图片数: {stats['total_image_count']}")
                print(f"   - 层级: {stats['level']}")
                print(f"   - 路径: {stats['path']}")
            
    except Exception as e:
        print(f"❌ 图集统计测试失败: {e}")


def test_gallery_search():
    """测试图集搜索"""
    print("\n=== 测试图集搜索 ===")
    
    try:
        with session_manager.get_session() as session:
            gallery_service = GalleryService(session)
            
            # 搜索图集
            results = gallery_service.search_galleries("山脉")
            print(f"🔍 搜索'山脉'找到 {len(results)} 个图集:")
            for gallery in results:
                print(f"   - {gallery.name}: {gallery.description}")
            
            # 按类型搜索
            album_results = gallery_service.search_galleries("", GalleryType.ALBUM)
            print(f"📁 相册类型图集有 {len(album_results)} 个:")
            for gallery in album_results:
                print(f"   - {gallery.name} ({gallery.gallery_type})")
            
    except Exception as e:
        print(f"❌ 图集搜索测试失败: {e}")


def main():
    """主函数"""
    print("=== 图集系统测试 ===\n")
    
    # 检查数据库类型
    database_url = os.getenv("DATABASE_URL", "sqlite:///./image_data.db")
    if "sqlite" in database_url:
        print("🗃️ 使用SQLite数据库")
    else:
        print(f"🔗 使用数据库: {database_url}")
    
    try:
        # 创建数据库表
        print("1. 创建数据库表...")
        create_tables()
        print("✅ 数据库表创建完成")
        
        # 等待一下确保数据库操作完成
        time.sleep(0.1)
        
        # 测试图集创建
        root_id, nature_id, mountain_id, city_id = test_gallery_creation()
        
        if root_id:
            # 测试图集树
            test_gallery_tree()
            
            # 测试图集图片管理
            test_gallery_images()
            
            # 测试图集标签
            test_gallery_tags()
            
            # 测试图集统计
            test_gallery_statistics()
            
            # 测试图集搜索
            test_gallery_search()
        
        print("\n🎉 图集系统测试完成！")
        
    except Exception as e:
        print(f"\n❌ 图集系统测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
