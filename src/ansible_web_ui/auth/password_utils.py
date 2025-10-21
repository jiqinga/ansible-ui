"""
密码工具模块

提供密码哈希和验证功能，处理bcrypt版本兼容性问题。
"""

import warnings
from typing import Union
from passlib.context import CryptContext
import bcrypt

# 抑制bcrypt版本警告
warnings.filterwarnings("ignore", message=".*bcrypt.*")


class PasswordManager:
    """
    密码管理器
    
    处理密码哈希和验证，解决版本兼容性问题。
    """
    
    def __init__(self):
        """初始化密码管理器"""
        try:
            # 尝试使用passlib
            self.pwd_context = CryptContext(
                schemes=["bcrypt"],
                deprecated="auto",
                bcrypt__rounds=12
            )
            self.use_passlib = True
        except Exception:
            # 如果passlib有问题，直接使用bcrypt
            self.use_passlib = False
    
    def hash_password(self, password: str) -> str:
        """
        生成密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希密码
        """
        if self.use_passlib:
            return self.pwd_context.hash(password)
        else:
            # 直接使用bcrypt
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否正确
        """
        if self.use_passlib:
            return self.pwd_context.verify(plain_password, hashed_password)
        else:
            # 直接使用bcrypt
            try:
                return bcrypt.checkpw(
                    plain_password.encode('utf-8'),
                    hashed_password.encode('utf-8')
                )
            except Exception:
                return False


# 创建全局密码管理器实例
_password_manager = PasswordManager()


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希密码
    """
    return _password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        bool: 密码是否正确
    """
    return _password_manager.verify_password(plain_password, hashed_password)