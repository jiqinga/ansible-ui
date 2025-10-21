"""
WebSocket连接管理器

管理WebSocket连接的生命周期和消息分发。
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from ansible_web_ui.schemas.execution_schemas import WebSocketMessage
from ansible_web_ui.utils.timezone import now

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebSocketClientInfo:
    """WebSocket客户端信息"""
    
    task_id: str
    user_id: Optional[int] = None
    connected_at: datetime = field(default_factory=now)


class WebSocketConnectionManager:
    """
    WebSocket连接管理器
    
    管理所有活跃的WebSocket连接，支持按任务ID分组和消息广播。
    """

    def __init__(self):
        """初始化连接管理器"""
        # 存储活跃连接：{task_id: {websocket: client_info}}
        self._connections: Dict[str, Dict[WebSocket, WebSocketClientInfo]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        task_id: str,
        user_id: Optional[int] = None
    ) -> None:
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            task_id: 任务ID
            user_id: 用户ID（可选）
        """
        await websocket.accept()
        
        async with self._lock:
            if task_id not in self._connections:
                self._connections[task_id] = {}
            
            client_info = WebSocketClientInfo(
                task_id=task_id,
                user_id=user_id,
                connected_at=now()
            )
            self._connections[task_id][websocket] = client_info
        
        logger.info(f"WebSocket连接已建立: task_id={task_id}, user_id={user_id}")

    async def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        """
        断开WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            task_id: 任务ID
        """
        async with self._lock:
            if task_id in self._connections:
                self._connections[task_id].pop(websocket, None)
                
                # 如果该任务没有连接了，删除任务记录
                if not self._connections[task_id]:
                    del self._connections[task_id]
        
        logger.info(f"WebSocket连接已断开: task_id={task_id}")

    async def send_message(
        self,
        task_id: str,
        message: str,
        websocket: Optional[WebSocket] = None
    ) -> None:
        """
        发送消息到指定任务的WebSocket连接
        
        Args:
            task_id: 任务ID
            message: 消息内容
            websocket: 特定的WebSocket连接（可选，如果不指定则广播给所有连接）
        """
        if task_id not in self._connections:
            # 降级为调试日志，因为任务可能在WebSocket连接建立前就开始执行
            logger.debug(f"📭 任务 {task_id} 暂无活跃的WebSocket连接")
            return

        payload = WebSocketMessage(
            type="log",
            task_id=task_id,
            data={"message": message},
            timestamp=now(),
        )

        if websocket:
            # 发送给特定连接
            await self._send(websocket, jsonable_encoder(payload))
        else:
            # 广播给所有连接
            await self.broadcast(task_id, jsonable_encoder(payload))

    async def send_status(
        self,
        task_id: str,
        status: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        发送状态更新
        
        Args:
            task_id: 任务ID
            status: 状态
            data: 额外数据
        """
        if task_id not in self._connections:
            return

        payload = WebSocketMessage(
            type="status",
            task_id=task_id,
            data={"status": status, **(data or {})},
            timestamp=now(),
        )
        
        await self.broadcast(task_id, jsonable_encoder(payload))

    async def send_error(
        self,
        task_id: str,
        error_message: str,
        error_code: Optional[str] = None
    ) -> None:
        """
        发送错误消息
        
        Args:
            task_id: 任务ID
            error_message: 错误消息
            error_code: 错误代码（可选）
        """
        if task_id not in self._connections:
            return

        payload = WebSocketMessage(
            type="error",
            task_id=task_id,
            data={
                "error_message": error_message,
                "error_code": error_code,
            },
            timestamp=now(),
        )
        
        await self.broadcast(task_id, jsonable_encoder(payload))

    async def broadcast(self, task_id: str, message: Any) -> None:
        """
        广播消息给指定任务的所有WebSocket连接
        
        Args:
            task_id: 任务ID
            message: 消息内容
        """
        if task_id not in self._connections:
            return

        # 获取所有连接的副本，避免在迭代时修改
        connections = list(self._connections[task_id].keys())
        
        # 并发发送消息
        tasks = [self._send(ws, message) for ws in connections]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _send(self, websocket: WebSocket, message: Any) -> None:
        """
        发送消息到单个WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            message: 消息内容
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")

    def get_active_connections(self, task_id: Optional[str] = None) -> int:
        """
        获取活跃连接数
        
        Args:
            task_id: 任务ID（可选，如果不指定则返回所有连接数）
            
        Returns:
            int: 连接数
        """
        if task_id:
            return len(self._connections.get(task_id, {}))
        return sum(len(conns) for conns in self._connections.values())

    def get_task_ids(self) -> Set[str]:
        """
        获取所有有活跃连接的任务ID
        
        Returns:
            Set[str]: 任务ID集合
        """
        return set(self._connections.keys())

    async def dispatch_event(self, payload: Dict[str, Any]) -> None:
        """
        分发事件到相应的WebSocket连接
        
        Args:
            payload: 事件负载，应包含 task_id 和其他事件数据
        """
        task_id = payload.get("task_id")
        if not task_id:
            logger.warning("⚠️ 收到没有 task_id 的事件")
            return

        # 检查是否有活跃连接
        if task_id not in self._connections:
            logger.debug(f"📭 任务 {task_id} 暂无WebSocket连接，跳过消息分发")
            return

        event_type = payload.get("type", "message")
        data = payload.get("data", {})
        
        # 根据事件类型分发
        if event_type == "log":
            # 日志事件：data 包含 message
            message = data.get("message", "")
            if message:
                await self.send_message(task_id, message)
        elif event_type == "status":
            # 状态事件：data 包含 status, progress, current_step 等
            status = data.get("status", "")
            await self.send_status(task_id, status, data)
        elif event_type == "error":
            # 错误事件
            error_message = data.get("error_message", "")
            error_code = data.get("error_code")
            await self.send_error(task_id, error_message, error_code)
        else:
            # 通用消息广播（直接发送整个 payload）
            await self.broadcast(task_id, payload)


# 全局WebSocket管理器实例
_websocket_manager: Optional[WebSocketConnectionManager] = None


def get_websocket_manager() -> WebSocketConnectionManager:
    """
    获取全局WebSocket管理器实例
    
    Returns:
        WebSocketConnectionManager: WebSocket管理器
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketConnectionManager()
    return _websocket_manager
