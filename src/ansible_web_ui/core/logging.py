"""日志配置模块

提供结构化日志记录，支持控制台输出、文件轮转与压缩归档。
使用 Rich 库增强终端输出效果。
"""

from __future__ import annotations

import gzip
import json
import logging
import os
import shutil
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

import structlog
import structlog.stdlib
import structlog.types
from structlog.processors import CallsiteParameter, CallsiteParameterAdder
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from ansible_web_ui.core.config import settings

_DEFAULT_LOG_FILENAME = "audit.jsonl"


def setup_logging(log_file: Optional[str] = None) -> None:
    """配置应用程序的结构化日志。"""

    log_path = _resolve_log_path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    retention_days = max(settings.LOG_RETENTION_DAYS, 1)
    pre_chain = _build_pre_chain()

    structlog.configure(
        processors=pre_chain
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    console_handler = _create_console_handler(pre_chain)
    file_handler = _create_file_handler(log_path, retention_days, pre_chain)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(_resolve_log_level(settings.LOG_LEVEL))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.captureWarnings(True)

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """获取结构化日志记录器。"""

    return structlog.get_logger(name)


def _resolve_log_path(log_file: Optional[str]) -> Path:
    if log_file:
        return Path(log_file)
    return Path(settings.LOG_DIR) / "audit" / _DEFAULT_LOG_FILENAME


def _resolve_log_level(level_name: str) -> int:
    level = getattr(logging, str(level_name).upper(), None)
    if isinstance(level, int):
        return level
    return logging.INFO


def _build_pre_chain() -> list[structlog.types.Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
        CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.MODULE,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
                CallsiteParameter.FILENAME,
            ]
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def _create_console_handler(
    pre_chain: list[structlog.types.Processor],
) -> logging.Handler:
    """创建控制台日志处理器，使用 Rich 增强输出"""
    
    # 检测是否支持彩色输出
    if settings.LOG_NO_COLOR or os.environ.get('LOG_NO_COLOR'):
        supports_color = False
    else:
        supports_color = _detect_color_support()
    
    # 在Windows上设置UTF-8编码
    if sys.platform == 'win32':
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    # 创建 Rich Console 实例
    console = Console(
        stderr=True,
        force_terminal=supports_color,
        force_interactive=False,
        color_system="auto" if supports_color else None,
        legacy_windows=False,  # 使用现代 Windows 终端支持
        theme=_create_rich_theme(),
    )
    
    # 使用 RichHandler 替代标准 StreamHandler
    rich_handler = RichHandler(
        console=console,
        show_time=False,  # structlog 已经添加了时间戳
        show_level=False,  # structlog 已经添加了日志级别
        show_path=False,  # structlog 已经添加了文件信息
        markup=True,  # 支持 Rich 标记语法
        rich_tracebacks=True,  # 使用 Rich 的美化异常追踪
        tracebacks_show_locals=True,  # 显示局部变量
        tracebacks_extra_lines=2,  # 额外显示的代码行数
        tracebacks_theme="monokai",  # 异常追踪主题
    )
    
    # 配置 structlog 格式化器
    rich_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=_create_rich_processor(supports_color),
            foreign_pre_chain=pre_chain,
        )
    )
    
    return rich_handler


def _create_rich_theme() -> Theme:
    """创建 Rich 主题配置"""
    return Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "critical": "bold white on red",
        "debug": "dim cyan",
        "success": "bold green",
        "timestamp": "dim white",
        "logger": "bold blue",
        "module": "magenta",
        "function": "green",
    })


def _create_rich_processor(supports_color: bool) -> structlog.types.Processor:
    """创建 Rich 增强的日志处理器"""
    
    def rich_processor(
        logger: logging.Logger,
        method_name: str,
        event_dict: structlog.types.EventDict,
    ) -> str:
        """使用 Rich 标记语法格式化日志"""
        
        # 提取关键字段
        timestamp = event_dict.pop("timestamp", "")
        level = event_dict.pop("level", "info").upper()
        event = event_dict.pop("event", "")
        logger_name = event_dict.pop("logger", "")
        
        # 提取调用位置信息
        module = event_dict.pop("module", "")
        func_name = event_dict.pop("func_name", "")
        lineno = event_dict.pop("lineno", "")
        filename = event_dict.pop("filename", "")
        
        # 根据日志级别选择颜色和emoji
        level_emoji = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🔥",
        }
        
        level_color = {
            "DEBUG": "dim cyan",
            "INFO": "cyan",
            "WARNING": "yellow",
            "ERROR": "bold red",
            "CRITICAL": "bold white on red",
        }
        
        emoji = level_emoji.get(level, "📝")
        color = level_color.get(level, "white")
        
        if not supports_color:
            # 无颜色模式：简洁输出
            parts = [
                timestamp,
                f"[{level}]",
                event,
            ]
            if logger_name:
                parts.append(f"[{logger_name}]")
            if module and func_name:
                parts.append(f"({module}.{func_name}:{lineno})")
            
            # 添加额外字段
            if event_dict:
                extra = " ".join(f"{k}={v}" for k, v in event_dict.items())
                parts.append(extra)
            
            return " ".join(parts)
        
        # 彩色模式：使用 Rich 标记
        parts = []
        
        # 时间戳
        if timestamp:
            parts.append(f"[dim]{timestamp}[/dim]")
        
        # 日志级别和emoji
        parts.append(f"{emoji} [{color}]{level:8}[/{color}]")
        
        # 事件消息
        if event:
            parts.append(f"[bold]{event}[/bold]")
        
        # Logger名称
        if logger_name:
            parts.append(f"[bold blue]\\[{logger_name}][/bold blue]")
        
        # 调用位置
        if module and func_name:
            parts.append(
                f"[dim]([magenta]{module}[/magenta]."
                f"[green]{func_name}[/green]:[yellow]{lineno}[/yellow])[/dim]"
            )
        
        # 额外字段
        if event_dict:
            extra_parts = []
            for k, v in event_dict.items():
                extra_parts.append(f"[cyan]{k}[/cyan]=[yellow]{v}[/yellow]")
            if extra_parts:
                parts.append(" ".join(extra_parts))
        
        return " ".join(parts)
    
    return rich_processor


def _detect_color_support() -> bool:
    """检测终端是否支持ANSI颜色代码"""
    # 检查是否是TTY
    if not (hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()):
        return False
    
    # Windows平台特殊处理
    if sys.platform == 'win32':
        # Windows Terminal
        if os.environ.get('WT_SESSION'):
            return True
        # ConEmu
        if os.environ.get('ConEmuANSI') == 'ON':
            return True
        # 检查是否启用了虚拟终端处理
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-12)  # STD_ERROR_HANDLE
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                return bool(mode.value & 0x0004)
        except Exception:
            pass
        return False
    
    # Unix/Linux/Mac平台
    term = os.environ.get('TERM', '')
    if term == 'dumb':
        return False
    
    # 检查COLORTERM环境变量
    if os.environ.get('COLORTERM'):
        return True
    
    # 常见支持颜色的终端
    color_terms = ('xterm', 'xterm-color', 'xterm-256color', 'screen', 
                   'screen-256color', 'tmux', 'tmux-256color', 'rxvt-unicode',
                   'rxvt-unicode-256color', 'linux', 'cygwin')
    
    return any(term.startswith(ct) for ct in color_terms)


def _create_file_handler(
    log_path: Path,
    retention_days: int,
    pre_chain: list[structlog.types.Processor],
) -> TimedRotatingFileHandler:
    file_handler = TimedRotatingFileHandler(
        filename=str(log_path),
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8",
        delay=True,
        utc=False,
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.namer = _rotated_file_namer
    file_handler.rotator = _gzip_rotator
    file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(
                sort_keys=False,
                serializer=lambda value, **_: json.dumps(
                    value, ensure_ascii=False, default=str
                ),
            ),
            foreign_pre_chain=pre_chain,
        )
    )
    return file_handler


def _rotated_file_namer(path: str) -> str:
    return f"{path}.gz"


def _gzip_rotator(source: str, destination: str) -> None:
    with open(source, "rb") as src, gzip.open(destination, "wb") as dst:
        shutil.copyfileobj(src, dst)
    Path(source).unlink(missing_ok=True)
