"""统一异常与错误码。

所有接口错误返回 {code, message, detail} 三件套（见技术文档 14 章）。
"""
from fastapi import HTTPException


class AppError(HTTPException):
    """业务异常基类，统一错误码前缀。"""

    def __init__(self, status_code: int, code: str, message: str, detail: str | None = None):
        super().__init__(status_code=status_code, detail={"code": code, "message": message, "detail": detail})
        self.code = code


# 认证相关错误码
def unauthorized(message: str = "未登录或令牌已失效") -> AppError:
    return AppError(401, "UNAUTHORIZED", message)


def forbidden(message: str = "没有权限") -> AppError:
    return AppError(403, "FORBIDDEN", message)


def not_found(message: str = "资源不存在") -> AppError:
    return AppError(404, "NOT_FOUND", message)


def conflict(message: str = "资源冲突") -> AppError:
    return AppError(409, "CONFLICT", message)
