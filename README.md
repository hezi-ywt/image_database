# 图片数据库管理系统

一个功能完整的图片数据库管理系统，支持图片管理、图集嵌套、标签系统和Caption管理。

## 🚀 主要功能

### 📸 图片管理
- **基础CRUD**：创建、读取、更新、删除图片
- **元数据管理**：文件大小、尺寸、哈希值、颜色空间等
- **重复检测**：基于哈希值的重复图片检测
- **相似图片**：基于感知哈希的相似图片查找

### 🗂️ 图集系统
- **嵌套图集**：支持无限层级的图集嵌套
- **图集类型**：Collection（普通）、Series（系列）、Album（相册）、Project（项目）
- **路径管理**：自动维护图集路径和层级深度
- **统计信息**：图片数量、子图集数量、总图片数量

### 🏷️ 标签系统
- **图集标签**：为图集添加标签分类
- **Caption标签**：图片描述和标签管理
- **多语言支持**：支持多种语言的Caption

### 📝 Caption管理
- **动态Caption类型**：用户可创建新的Caption类型
- **多Caption支持**：一张图片可以有多个不同类型的Caption
- **语言代码**：标准化的语言代码枚举
- **置信度**：Caption的置信度评分

## 📁 项目结构

```
image_data/
├── model/                          # 数据模型
│   ├── base.py                     # 数据库基础配置
│   ├── images.py                   # 图片模型
│   ├── metadata.py                 # 图片元数据模型
│   ├── caption.py                  # Caption模型
│   ├── gallery.py                  # 图集模型
│   ├── images_service.py           # 图片服务类
│   ├── caption_service.py          # Caption服务类
│   ├── gallery_service.py          # 图集服务类
│   ├── session_manager.py          # 会话管理器
│   └── __init__.py                 # 模块导入
├── test_gallery_system.py          # 图集系统测试
├── batch_load_caption.py           # 批量加载脚本
└── README.md                       # 项目说明
```

## 🗄️ 数据库设计

### 核心表结构

#### 1. **Images（图片表）**
```sql
- id: 主键
- file_path: 文件路径
- description: 图片描述
- created_at/updated_at/deleted_at: 时间戳
```

#### 2. **Images_metadata（图片元数据表）**
```sql
- id: 主键
- image_id: 图片ID（外键）
- file_size: 文件大小
- mime_type: MIME类型
- image_hash: 图片哈希
- perceptual_hash: 感知哈希
- image_width/height: 图片尺寸
- color_space: 颜色空间
- bit_depth: 位深度
- has_transparency: 是否有透明度
- file_checksum: 文件校验和
- is_corrupted: 是否损坏
```

#### 3. **Galleries（图集表）**
```sql
- id: 主键
- name: 图集名称
- description: 图集描述
- gallery_type: 图集类型
- parent_id: 父图集ID（自引用）
- level: 层级深度
- path: 图集路径
- image_count: 图片数量
- sub_gallery_count: 子图集数量
- total_image_count: 总图片数量
- cover_image_id: 封面图片ID
- sort_order: 排序顺序
- is_public: 是否公开
```

#### 4. **Gallery_images（图集图片关联表）**
```sql
- id: 主键
- gallery_id: 图集ID
- image_id: 图片ID
- sort_order: 排序顺序
- is_cover: 是否为封面
- is_featured: 是否为精选
```

#### 5. **Caption相关表**
```sql
- caption_types: Caption类型表
- image_captions: 图片Caption表
- gallery_tags: 图集标签表
- gallery_tag_associations: 图集标签关联表
```

## 🛠️ 安装和配置

### 1. 安装依赖
```bash
pip install sqlalchemy psycopg2-binary
```

### 2. 数据库配置
支持SQLite和PostgreSQL：

#### SQLite（默认）
```python
DATABASE_URL = "sqlite:///./image_data.db"
```

#### PostgreSQL
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/image_data"
```

### 3. 创建数据库表
```python
from model.base import create_tables
create_tables()
```

## 📖 使用示例

### 基础图片管理
```python
from model.session_manager import session_manager
from model.images_service import ImagesService
from model.caption_service import CaptionService
from model.caption import LanguageCode

# 创建图片
with session_manager.get_session() as session:
    image_service = ImagesService(session)
    caption_service = CaptionService(session)
    
    # 创建图片
    image = image_service.create_image("/path/to/image.jpg", "图片描述")
    
    # 添加Caption
    caption = caption_service.add_caption(
        image_id=image.id,
        caption_type_name="description",
        content="这是一张美丽的风景照片",
        language=LanguageCode.ZH,
        is_primary=True
    )
```

### 图集管理
```python
from model.gallery_service import GalleryService
from model.gallery import GalleryType

# 创建图集
with session_manager.get_session() as session:
    gallery_service = GalleryService(session)
    
    # 创建根图集
    root_gallery = gallery_service.create_gallery(
        name="我的图库",
        description="个人图片收藏",
        gallery_type=GalleryType.COLLECTION
    )
    
    # 创建子图集
    nature_gallery = gallery_service.create_gallery(
        name="自然风光",
        description="自然风景照片",
        gallery_type=GalleryType.ALBUM,
        parent_id=root_gallery.id
    )
    
    # 添加图片到图集
    gallery_service.add_image_to_gallery(
        gallery_id=nature_gallery.id,
        image_id=image.id,
        sort_order=0,
        is_cover=True
    )
    
    # 获取图集树
    tree = gallery_service.get_gallery_tree()
```

### 批量加载
```python
# 批量加载图片和Caption
from batch_load_caption import load_image_caption_from_dir

# 从目录加载
load_image_caption_from_dir("/path/to/images")
```

## 🧪 测试

### 运行图集系统测试
```bash
python test_gallery_system.py
```

### 运行批量加载测试
```bash
python batch_load_caption.py
```

## 🔧 高级功能

### 1. 重复图片检测
```python
from model.image_util import find_duplicate_images, find_similar_images

# 查找重复图片
duplicates = find_duplicate_images(session)

# 查找相似图片
similar = find_similar_images(session, image_id, threshold=10)
```

### 2. 图集搜索
```python
# 搜索图集
results = gallery_service.search_galleries("风景")

# 按类型搜索
albums = gallery_service.search_galleries("", GalleryType.ALBUM)
```

### 3. 统计信息
```python
# 获取图集统计
stats = gallery_service.get_gallery_statistics(gallery_id)
print(f"图片数量: {stats['total_image_count']}")
```

## 🏗️ 架构设计

### 服务层设计
- **ImagesService**：图片管理服务
- **CaptionService**：Caption管理服务
- **GalleryService**：图集管理服务
- **SessionManager**：统一会话管理

### 数据模型设计
- **BaseMixin**：通用字段（ID、时间戳、软删除）
- **关系映射**：一对多、多对多关系
- **枚举类型**：标准化的枚举值

### 会话管理
- **依赖注入**：服务类通过构造函数注入Session
- **上下文管理**：自动管理数据库连接和事务
- **错误处理**：统一的异常处理机制

## 🚀 性能优化

### SQLite优化
- **WAL模式**：提高并发性能
- **连接池**：优化连接管理
- **重试机制**：处理数据库锁定

### PostgreSQL支持
- **连接池**：高效的连接管理
- **索引优化**：提高查询性能
- **事务管理**：ACID特性保证

## 📝 开发指南

### 添加新功能
1. 在`model/`目录下创建新的模型文件
2. 创建对应的服务类
3. 更新`__init__.py`导入
4. 编写测试用例

### 数据库迁移
1. 修改模型定义
2. 运行`create_tables()`重新创建表
3. 处理数据迁移（如需要）

### 错误处理
- 使用统一的异常处理
- 提供详细的错误信息
- 支持重试机制

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

MIT License

## 🆘 支持

如有问题，请创建Issue或联系开发者。

---

**注意**：本系统支持SQLite和PostgreSQL，建议在生产环境中使用PostgreSQL以获得更好的性能和并发支持。