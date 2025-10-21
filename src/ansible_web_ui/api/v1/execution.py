"""
🚀 任务执行API端点

提供Ansible任务执行、状态查询、取消等功能的RESTful API接口。
"""

import logging
from datetime import datetime
from typing import List, Optional

from ansible_web_ui.utils.timezone import now

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_db_session
from ansible_web_ui.auth.dependencies import get_current_active_user as get_current_user
from ansible_web_ui.models.user import User
from ansible_web_ui.schemas.execution_schemas import (
    ExecutePlaybookRequest,
    TaskStatusResponse,
    TaskResultResponse,
    TaskLogResponse,
    TaskListResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    ValidatePlaybookRequest,
    ValidatePlaybookResponse,
    TestConnectionRequest,
    TestConnectionResponse,
    WebSocketMessage
)
from ansible_web_ui.tasks.ansible_tasks import (
    run_playbook_task,
    validate_playbook_task,
    test_connection_task,
    cancel_playbook_task
)
from ansible_web_ui.tasks.task_tracker import get_task_tracker
from ansible_web_ui.services.ansible_execution_service import get_ansible_execution_service

logger = logging.getLogger(__name__)
security = HTTPBearer()

# 创建路由器
router = APIRouter(prefix="/execution", tags=["任务执行"])

# 使用统一的WebSocket管理器
from ansible_web_ui.websocket.manager import get_websocket_manager

# 获取全局管理器实例
manager = get_websocket_manager()


@router.post("/playbook", response_model=TaskStatusResponse, summary="🚀 执行Playbook")
async def execute_playbook(
    request: ExecutePlaybookRequest,
    current_user: User = Depends(get_current_user)
):
    """
    执行Ansible Playbook
    
    启动一个异步任务来执行指定的Playbook，返回任务ID用于后续状态查询。
    
    - **playbook_name**: Playbook文件名
    - **inventory_targets**: 目标主机列表
    - **execution_options**: 执行选项配置
    """
    try:
        logger.info(f"用户 {current_user.username} 请求执行Playbook: {request.playbook_name}")
        
        # 先创建任务跟踪记录，获取task_id
        task_tracker = get_task_tracker()
        task_id = task_tracker.create_task(
            task_name=f"执行Playbook: {request.playbook_name}",
            user_id=current_user.id,
            playbook_name=request.playbook_name,
            inventory_targets=request.inventory_targets
        )
        
        # 准备任务参数
        task_kwargs = {
            "playbook_name": request.playbook_name,
            "inventory_targets": request.inventory_targets,
            "user_id": current_user.id,
            "execution_options": request.execution_options.model_dump() if request.execution_options else None
        }
        
        # 使用指定的task_id启动异步任务
        task_result = run_playbook_task.apply_async(kwargs=task_kwargs, task_id=task_id)
        
        logger.info(f"Playbook执行任务已启动: {task_id}")
        
        return TaskStatusResponse(
            task_id=task_id,
            task_name=f"执行Playbook: {request.playbook_name}",
            status="PENDING",
            progress=0,
            current_step="任务已提交，等待执行"
        )
        
    except Exception as e:
        logger.error(f"启动Playbook执行任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"启动任务失败: {str(e)}"
        )


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse, summary="📊 查询任务状态")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    查询任务执行状态
    
    根据任务ID查询任务的当前执行状态、进度和相关信息。
    
    - **task_id**: 任务ID
    """
    try:
        task_tracker = get_task_tracker()
        task_info = task_tracker.get_task_info(task_id)
        
        if not task_info:
            raise HTTPException(
                status_code=404,
                detail=f"任务不存在: {task_id}"
            )
        
        # 计算执行时长
        duration = None
        if task_info.start_time and task_info.end_time:
            duration = (task_info.end_time - task_info.start_time).total_seconds()
        
        return TaskStatusResponse(
            task_id=task_info.task_id,
            task_name=task_info.task_name,
            status=task_info.status,
            progress=task_info.progress,
            current_step=task_info.current_step,
            start_time=task_info.start_time,
            end_time=task_info.end_time,
            duration=duration,
            error_message=task_info.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务状态失败: {task_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"查询任务状态失败: {str(e)}"
        )


@router.get("/tasks/{task_id}/result", response_model=TaskResultResponse, summary="📋 获取任务结果")
async def get_task_result(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取任务执行结果
    
    获取已完成任务的详细执行结果，包括统计信息、日志文件路径等。
    
    - **task_id**: 任务ID
    """
    try:
        task_tracker = get_task_tracker()
        task_info = task_tracker.get_task_info(task_id)
        
        if not task_info:
            raise HTTPException(
                status_code=404,
                detail=f"任务不存在: {task_id}"
            )
        
        if task_info.status not in ["SUCCESS", "FAILURE", "REVOKED"]:
            raise HTTPException(
                status_code=400,
                detail=f"任务尚未完成，当前状态: {task_info.status}"
            )
        
        # 计算执行时长
        duration = None
        if task_info.start_time and task_info.end_time:
            duration = (task_info.end_time - task_info.start_time).total_seconds()
        
        # 从结果中提取详细信息
        result_data = task_info.result or {}
        
        return TaskResultResponse(
            task_id=task_info.task_id,
            playbook_name=task_info.playbook_name or "未知",
            status=task_info.status,
            exit_code=result_data.get("exit_code"),
            start_time=task_info.start_time,
            end_time=task_info.end_time,
            duration=duration,
            stats=result_data.get("stats"),
            log_file_path=result_data.get("log_file_path"),
            error_message=task_info.error_message,
            failed_tasks=result_data.get("failed_tasks")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务结果失败: {task_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务结果失败: {str(e)}"
        )


@router.get("/tasks/{task_id}/logs", response_model=TaskLogResponse, summary="📝 获取任务日志")
async def get_task_logs(
    task_id: str,
    limit: int = Query(100, description="日志条目限制", ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    获取任务执行日志
    
    获取任务执行过程中的实时日志信息。
    
    - **task_id**: 任务ID
    - **limit**: 日志条目数量限制
    """
    try:
        task_tracker = get_task_tracker()
        
        # 验证任务存在
        task_info = task_tracker.get_task_info(task_id)
        if not task_info:
            raise HTTPException(
                status_code=404,
                detail=f"任务不存在: {task_id}"
            )
        
        # 获取日志
        logs = task_tracker.get_task_logs(task_id, limit)
        
        return TaskLogResponse(
            task_id=task_id,
            logs=logs,
            total_count=len(logs)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务日志失败: {task_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务日志失败: {str(e)}"
        )


@router.get("/tasks", response_model=TaskListResponse, summary="📋 获取任务列表")
async def get_task_list(
    status: Optional[str] = Query(None, description="状态过滤器"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页大小", ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户任务列表
    
    获取当前用户的任务列表，支持状态过滤和分页。
    
    - **status**: 状态过滤器（可选）
    - **page**: 页码
    - **page_size**: 每页大小
    """
    try:
        task_tracker = get_task_tracker()
        
        # 获取用户任务
        all_tasks = task_tracker.get_user_tasks(
            user_id=current_user.id,
            status_filter=status,
            limit=page_size * 10  # 获取更多数据用于分页
        )
        
        # 计算分页
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        page_tasks = all_tasks[start_index:end_index]
        
        # 转换为响应格式
        task_responses = []
        for task_info in page_tasks:
            duration = None
            if task_info.start_time and task_info.end_time:
                duration = (task_info.end_time - task_info.start_time).total_seconds()
            
            task_responses.append(TaskStatusResponse(
                task_id=task_info.task_id,
                task_name=task_info.task_name,
                status=task_info.status,
                progress=task_info.progress,
                current_step=task_info.current_step,
                start_time=task_info.start_time,
                end_time=task_info.end_time,
                duration=duration,
                error_message=task_info.error_message
            ))
        
        return TaskListResponse(
            tasks=task_responses,
            total_count=len(all_tasks),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.post("/tasks/{task_id}/cancel", response_model=CancelTaskResponse, summary="🛑 取消任务")
async def cancel_task(
    task_id: str,
    request: CancelTaskRequest,
    current_user: User = Depends(get_current_user)
):
    """
    取消正在执行的任务
    
    取消指定的任务执行，只能取消正在运行或等待中的任务。
    
    - **task_id**: 任务ID
    - **reason**: 取消原因（可选）
    """
    try:
        task_tracker = get_task_tracker()
        
        # 验证任务存在
        task_info = task_tracker.get_task_info(task_id)
        if not task_info:
            raise HTTPException(
                status_code=404,
                detail=f"任务不存在: {task_id}"
            )
        
        # 检查任务状态
        if task_info.status in ["SUCCESS", "FAILURE", "REVOKED"]:
            return CancelTaskResponse(
                success=False,
                message=f"任务已完成，无法取消。当前状态: {task_info.status}",
                task_id=task_id
            )
        
        # 记录取消原因
        if request.reason:
            task_tracker.add_log_entry(task_id, f"🛑 用户取消任务，原因: {request.reason}")
        
        # 取消任务
        success = task_tracker.cancel_task(task_id)
        
        if success:
            logger.info(f"用户 {current_user.username} 取消任务: {task_id}")
            return CancelTaskResponse(
                success=True,
                message="任务已成功取消",
                task_id=task_id
            )
        else:
            return CancelTaskResponse(
                success=False,
                message="任务取消失败，请稍后重试",
                task_id=task_id
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {task_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"取消任务失败: {str(e)}"
        )


@router.post("/validate", response_model=ValidatePlaybookResponse, summary="✅ 验证Playbook语法")
async def validate_playbook(
    request: ValidatePlaybookRequest,
    current_user: User = Depends(get_current_user)
):
    """
    验证Playbook语法
    
    验证指定Playbook文件的YAML语法和Ansible结构是否正确。
    
    - **playbook_name**: Playbook文件名
    """
    try:
        logger.info(f"用户 {current_user.username} 请求验证Playbook: {request.playbook_name}")
        
        # 启动验证任务
        task_result = validate_playbook_task.delay(request.playbook_name)
        
        # 等待验证结果（验证通常很快）
        result = task_result.get(timeout=30)
        
        return ValidatePlaybookResponse(**result)
        
    except Exception as e:
        logger.error(f"验证Playbook失败: {request.playbook_name}, 错误: {str(e)}")
        return ValidatePlaybookResponse(
            valid=False,
            errors=[f"验证过程中发生错误: {str(e)}"],
            warnings=[],
            message="验证失败"
        )


@router.post("/test-connection", response_model=TestConnectionResponse, summary="🔗 测试主机连接")
async def test_connection(
    request: TestConnectionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    测试主机连接性
    
    测试指定主机列表的连接性，使用Ansible ping模块进行测试。
    
    - **inventory_targets**: 目标主机列表
    """
    try:
        logger.info(f"用户 {current_user.username} 请求测试主机连接: {request.inventory_targets}")
        
        # 启动连接测试任务
        task_result = test_connection_task.delay(request.inventory_targets)
        
        # 等待测试结果
        result = task_result.get(timeout=60)
        
        return TestConnectionResponse(**result)
        
    except Exception as e:
        logger.error(f"测试主机连接失败: {request.inventory_targets}, 错误: {str(e)}")
        return TestConnectionResponse(
            total_hosts=len(request.inventory_targets),
            successful_hosts=[],
            failed_hosts=request.inventory_targets,
            success_rate=0,
            message=f"连接测试失败: {str(e)}"
        )


@router.websocket("/tasks/{task_id}/logs/stream")
async def websocket_task_logs(
    websocket: WebSocket, 
    task_id: str,
    token: str = None
):
    """
    WebSocket实时日志流
    
    通过WebSocket连接实时推送任务执行日志。
    
    - **task_id**: 任务ID
    - **token**: 认证令牌（通过查询参数传递）
    """
    # 验证token（可选，如果需要认证）
    user_id = None
    if token:
        try:
            from ansible_web_ui.auth.security import verify_token
            payload = verify_token(token)
            user_id = int(payload.get("sub"))
        except Exception as e:
            logger.warning(f"WebSocket认证失败: {e}")
            # 继续连接，但不设置user_id
    
    # 建立连接
    await manager.connect(websocket, task_id, user_id=user_id)
    
    try:
        # 发送连接成功消息
        from ansible_web_ui.schemas.execution_schemas import WebSocketMessage
        connected_msg = WebSocketMessage(
            type="connected",
            task_id=task_id,
            data={"message": "WebSocket连接已建立"},
            timestamp=now()
        )
        await websocket.send_json(connected_msg.model_dump(mode='json'))
        
        # 发送历史日志
        task_tracker = get_task_tracker()
        existing_logs = task_tracker.get_task_logs(task_id, limit=50)
        
        for log_entry in existing_logs:
            log_msg = WebSocketMessage(
                type="log",
                task_id=task_id,
                data={"message": log_entry},
                timestamp=now()
            )
            await websocket.send_json(log_msg.model_dump(mode='json'))
        
        # 保持连接活跃
        while True:
            try:
                # 等待客户端消息（心跳包）
                data = await websocket.receive_text()
                
                # 响应心跳包
                if data == "ping":
                    pong_msg = WebSocketMessage(
                        type="pong",
                        task_id=task_id,
                        data={"message": "连接正常"},
                        timestamp=now()
                    )
                    await websocket.send_json(pong_msg.model_dump(mode='json'))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket处理消息失败: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
    finally:
        await manager.disconnect(websocket, task_id)



@router.get("/host/{hostname}/history", summary="📜 获取主机执行历史")
async def get_host_execution_history(
    hostname: str,
    limit: int = Query(5, ge=1, le=50, description="返回记录数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取指定主机的执行历史记录
    
    Args:
        hostname: 主机名或IP地址
        limit: 限制返回的记录数（默认5条，最多50条）
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        执行历史记录列表
    """
    try:
        # 获取执行历史服务
        from ansible_web_ui.services.execution_history_service import ExecutionHistoryService
        
        service = ExecutionHistoryService(db)
        executions = await service.get_host_execution_history(hostname, limit)
        
        # 转换为响应格式
        result = []
        for execution in executions:
            result.append({
                "id": execution.id,
                "task_id": execution.task_id,
                "playbook_name": execution.playbook_name,
                "status": execution.status.value,
                "start_time": execution.start_time.isoformat() if execution.start_time else None,
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "duration": execution.duration,
                "created_at": execution.created_at.isoformat(),
                "user": {
                    "id": execution.user.id,
                    "username": execution.user.username
                } if execution.user else None
            })
        
        return {
            "executions": result,
            "total": len(result),
            "hostname": hostname
        }
            
    except Exception as e:
        logger.error(f"获取主机执行历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取执行历史失败: {str(e)}")
