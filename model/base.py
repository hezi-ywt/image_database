from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./image_data.db")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设置为True可以看到SQL语句
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=3600,   # 连接回收时间
    connect_args={
        "check_same_thread": False,  # 允许多线程访问
        "timeout": 30,              # 连接超时时间
        "isolation_level": None,     # 自动提交模式，减少锁定
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

class BaseMixin:
    """model的基类,所有model都必须继承"""
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, index=True)
    deleted_at = Column(DateTime)  # 可以为空, 如果非空, 则为软删

def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话的依赖注入函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
