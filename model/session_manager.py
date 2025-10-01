#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理器 - 统一管理数据库连接
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from .base import SessionLocal


class SessionManager:
    """数据库会话管理器"""
    
    @staticmethod
    @contextmanager
    def get_session() -> Generator[Session, None, None]:
        """获取数据库会话的上下文管理器
        
        Yields:
            Session: 数据库会话
        """
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @staticmethod
    def get_session_factory():
        """获取会话工厂"""
        return SessionLocal


# 全局会话管理器实例
session_manager = SessionManager()
