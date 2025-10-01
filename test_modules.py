from model.service import ImagesService
from model.base import create_tables


if __name__ == "__main__":
    # 首先创建数据库表
    print("创建数据库表...")
    create_tables()
    print("数据库表创建完成！")
    
    # 使用上下文管理器
    with ImagesService() as service:
        print("创建图片...")
        image = service.create_image("test.jpg", "test")
        print(f"创建成功: ID={image.id}")
        
        print("查询图片...")
        found_image = service.get_by_id(image.id)
        if found_image:
            print(f"查询成功: {found_image.description}")
        else:
            print("查询失败")