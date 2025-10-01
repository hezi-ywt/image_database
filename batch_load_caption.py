from model import ImagesService, CaptionService
from model.session_manager import session_manager

import time
import json
import os
from tqdm import tqdm



def load_image_caption_with_retry(image_path: str, caption_content: str, caption_type: str, 
                                 Imageservice: ImagesService, Captionservice: CaptionService, 
                                 max_retries=3):
    """带重试机制的加载函数"""
    
    for attempt in range(max_retries):
        try:
            # 创建图片
            image = Imageservice.create_image(image_path, description="批量加载的图片")
            
            # 创建caption
            caption = Captionservice.add_caption(
                image_id=image.id, 
                caption_type_name=caption_type, 
                content=caption_content
            )
            return image, caption
            
        except Exception as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"数据库被锁定，重试 {attempt + 1}/{max_retries}...")
                time.sleep(0.1 * (2 ** attempt))  # 指数退避
                continue
            else:
                raise e
def is_image_file(file_path: str) -> bool:
    """判断是否为图片文件"""
    return file_path.endswith(".jpg") or file_path.endswith(".png") or file_path.endswith(".jpeg") or file_path.endswith(".webp")

CAPTION_TYPES = ["wd_tagger", "gemini_caption_v2", "regular_summary", "short_summary", "detailed_description"]


def load_json_file(json_file_path: str) -> dict:
    """加载json文件"""
    with open(json_file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_json_caption(json_caption: dict, caption_dict: dict = {}, prefix: str = "") -> dict:
    """加载json文件"""
    for key, value in json_caption.items():
        if isinstance(value, dict):
            caption_dict = load_json_caption(value, caption_dict, prefix + key + "_")
        elif isinstance(value, str):
            caption_dict[prefix + key] = value
        else:
            print(f"❌ 未知类型: {type(value)}")
    return caption_dict
    

def load_image_caption_from_dir(dir_path: str, is_description: bool = True, verbose: bool = True, max_retries: int = 3, Imageservice: ImagesService = None, Captionservice: CaptionService = None):
    """从目录中加载图片和caption"""
    for dir, subdir, files in tqdm(os.walk(dir_path)):
        for file in files:
            if is_image_file(file):
                image_path = os.path.join(dir, file)
                json_caption_file = os.path.join(dir, os.path.splitext(file)[0] + ".json")
                if os.path.exists(json_caption_file):
                    json_caption = load_json_file(json_caption_file)
                    caption_dict = load_json_caption(json_caption)
                    image = Imageservice.create_image(image_path, description="批量加载的图片")
                    for key, value in caption_dict.items():
                        for attempt in range(max_retries):
                            caption = Captionservice.add_caption(
                                image_id=image.id, 
                                caption_type_name=key, 
                                content=value
                            )
                            if verbose:
                                print(f"✅ 创建caption: ID={caption.id}, 内容={caption.content}")
                            break
                                
    

if __name__ == "__main__":
    from model.base import create_tables
    import time
    import os
    
    # 检查数据库类型
    database_url = os.getenv("DATABASE_URL", "sqlite:///./image_data.db")
    if "postgresql" in database_url:
        print("🐘 使用PostgreSQL数据库")
    elif "sqlite" in database_url:
        print("🗃️ 使用SQLite数据库")
    else:
        print(f"🔗 使用数据库: {database_url}")
    
    try:
        # 创建数据库表
        print("正在创建数据库表...")
        create_tables()
        print("数据库表创建完成！")
        
        # 等待一下确保数据库操作完成
        time.sleep(0.1)
        
        # 使用会话管理器
        print("开始创建图片和caption...")
        with session_manager.get_session() as session:
            image_service = ImagesService(session)
            caption_service = CaptionService(session)
            
            # image, caption = load_image_caption_with_retry(
            #     "test.jpg", 
            #     "这是一张测试图片", 
            #     "description", 
            #     image_service, 
            #     caption_service
            # )
            # print(f"✅ 创建图片: ID={image.id}")
            # print(f"✅ 创建caption: ID={caption.id}, 内容={caption.content}")
            load_image_caption_from_dir("z:/DATA/diffusion/artist/add_new/wlop大神鬼刀_4k_filtered_webp",
                                        verbose=False,
                                        Imageservice=image_service,
                                        Captionservice=caption_service)
        print("🎉 操作完成！")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        if "database is locked" in str(e):
            print("💡 提示：SQLite数据库被锁定，建议切换到PostgreSQL")
            print("   运行: python setup_postgresql.py")
        elif "connection" in str(e).lower():
            print("💡 提示：数据库连接失败，请检查PostgreSQL是否运行")
            print("   运行: python setup_postgresql.py")
        import traceback
        traceback.print_exc()