"""日志相关的Pydantic模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class LogEntrySchema(BaseModel):
    """单条结构化日志记录。"""

    timestamp: datetime = Field(..., description="日志时间戳")
    level: str = Field(..., description="日志级别")
    event: str = Field(..., description="事件名称或简述")
    message: str = Field(..., description="日志原始消息")
    logger: str = Field(..., description="日志记录器名称")
    module: Optional[str] = Field(None, description="模块名称")
    function: Optional[str] = Field(None, description="函数名称")
    line: Optional[int] = Field(None, description="代码行号")
    request_id: Optional[str] = Field(None, description="关联的请求ID")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外的上下文字段"
    )

    @field_validator("level", mode="before")
    @classmethod
    def _normalize_level(cls, value: str) -> str:
        return str(value).upper()


class LogQueryFilters(BaseModel):
    """日志查询过滤条件。"""

    levels: Optional[List[str]] = Field(
        default=None,
        description="需要匹配的日志级别列表（例如 INFO、ERROR）",
    )
    start_time: Optional[datetime] = Field(
        default=None,
        description="起始时间（包含）",
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="结束时间（包含）",
    )
    keyword: Optional[str] = Field(
        default=None,
        description="匹配消息或上下文的关键字",
    )
    logger: Optional[str] = Field(
        default=None,
        description="限定的日志记录器名称",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="关联的请求ID",
    )
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(
        default=20,
        ge=1,
        le=200,
        description="每页返回的日志条数",
    )

    @field_validator("levels")
    @classmethod
    def _normalize_levels(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value:
            return [item.upper() for item in value if item]
        return None

    @model_validator(mode="after")
    def _validate_time_range(self) -> "LogQueryFilters":
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("start_time 不能晚于 end_time")
        return self


class LogQueryResponse(BaseModel):
    """日志查询响应。"""

    total: int = Field(..., description="符合条件的日志总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    items: List[LogEntrySchema] = Field(
        default_factory=list,
        description="日志记录列表"
    )
    has_more: bool = Field(
        default=False,
        description="是否还有更多结果可供分页加载"
    )
    available_levels: List[str] = Field(
        default_factory=list,
        description="当前结果集中出现的日志级别列表"
    )
