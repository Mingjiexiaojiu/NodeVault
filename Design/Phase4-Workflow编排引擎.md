# Phase 4 — Workflow 编排引擎

> **周期：约 8 周**
> **目标：让多个 Node 可以被编排成有向无环图（DAG），实现复杂的 AI 能力流水线**

---

## 核心思想

> 单个 Node 是原子能力，Workflow 是把原子能力组合成复合能力的方式。

Phase 4 将 NodeVault 从"能力仓库"进化为"能力编排平台"：

```
数据清洗 Node → 资金分析 Node → 风险评分 Node → 报告生成 Node
这条链路，可以定义为一个 Workflow，一次触发，自动执行完整。
```

Workflow 引擎参考 Apache Airflow 的设计哲学，但专注于 **AI Node 编排**，更轻量、更易用。

---

## 一、Workflow 核心概念

### 1.1 基本概念定义

| 概念 | 定义 | 类比 |
|------|------|------|
| **Workflow** | 一组 Node 组成的有向无环图（DAG） | 工厂流水线 |
| **Step** | Workflow 中的一个节点，对应一个 Node 调用 | 流水线上的工位 |
| **Edge** | Step 之间的依赖关系（有向边） | 物料传送带 |
| **WorkflowRun** | Workflow 的一次执行实例 | 一批生产任务 |
| **StepRun** | 单个 Step 的执行记录 | 单个工位的生产记录 |
| **Context** | 整个 Workflow 执行期间的共享数据 | 工单/随行文件 |

### 1.2 数据流模型

```
Workflow 触发（带初始 input）
          │
          ▼
     Step A 执行
     input: workflow.input
     output: → 存入 context["step_a"]
          │
    ┌─────┴──────┐
    ▼            ▼
  Step B        Step C      （并行执行）
  input: context["step_a"]  input: context["step_a"]
  output: context["step_b"] output: context["step_c"]
    │            │
    └─────┬──────┘
          ▼
        Step D              （需要 B 和 C 都完成）
        input: {
          "from_b": context["step_b"],
          "from_c": context["step_c"]
        }
        output: context["step_d"]
          │
          ▼
      Workflow 结束
      返回 context["step_d"]（或指定的 output_step）
```

---

## 二、Workflow Schema 设计

### 2.1 Workflow 定义格式（JSON）

```json
{
  "name": "fund_risk_analysis_pipeline",
  "version": "1.0.0",
  "description": "完整的资金风险分析流水线：清洗 → 分析 → 评分 → 报告",

  "input_schema": {
    "type": "object",
    "properties": {
      "raw_transactions": {"type": "array", "description": "原始交易数据"},
      "report_format": {"type": "string", "default": "json"}
    },
    "required": ["raw_transactions"]
  },

  "output_step": "generate_report",

  "steps": [
    {
      "id": "clean_data",
      "node": "clean_transaction_data",
      "node_version": "1.0.0",
      "description": "清洗原始交易数据",
      "input_mapping": {
        "data": "$.input.raw_transactions"
      },
      "depends_on": [],
      "retry": {"max_attempts": 2},
      "timeout": "60s"
    },
    {
      "id": "analyze_flow",
      "node": "analyze_capital_flow",
      "node_version": "latest",
      "description": "分析资金流向",
      "input_mapping": {
        "transactions": "$.steps.clean_data.output.result"
      },
      "depends_on": ["clean_data"],
      "timeout": "120s"
    },
    {
      "id": "detect_pool",
      "node": "detect_fund_pool",
      "description": "检测资金池",
      "input_mapping": {
        "transactions": "$.steps.clean_data.output.result",
        "threshold": 0.7
      },
      "depends_on": ["clean_data"],
      "timeout": "30s"
    },
    {
      "id": "risk_score",
      "node": "calculate_risk_score",
      "description": "计算综合风险评分",
      "input_mapping": {
        "flow_analysis": "$.steps.analyze_flow.output",
        "fund_pool_result": "$.steps.detect_pool.output",
        "account_count": "$.steps.clean_data.output.account_count"
      },
      "depends_on": ["analyze_flow", "detect_pool"],
      "timeout": "30s"
    },
    {
      "id": "generate_report",
      "node": "generate_risk_report",
      "description": "生成风险分析报告",
      "input_mapping": {
        "risk_score": "$.steps.risk_score.output.score",
        "details": "$.steps.risk_score.output",
        "format": "$.input.report_format"
      },
      "depends_on": ["risk_score"],
      "timeout": "30s"
    }
  ],

  "error_strategy": "fail_fast",
  "max_parallel_steps": 5,
  "timeout": "600s"
}
```

### 2.2 Input Mapping 语法

NodeVault Workflow 使用 JSONPath 风格的映射语法：

```
$.input.{field}              → 从 Workflow 的初始输入取值
$.steps.{step_id}.output.{field} → 从某个 Step 的输出取值
$.steps.{step_id}.status    → Step 的执行状态
{literal_value}             → 直接使用字面量值
```

---

## 三、数据库模型扩展

```python
# models/workflow.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("namespaces.id"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    description = Column(Text)
    status = Column(String(32), default="draft")   # draft | active | archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("WorkflowVersion", back_populates="workflow")
    runs = relationship("WorkflowRun", back_populates="workflow")


class WorkflowVersion(Base):
    __tablename__ = "workflow_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    version = Column(String(32), nullable=False)
    dag_definition = Column(JSONB, nullable=False)    # 完整的 DAG JSON
    is_default = Column(String(8), default=False)
    changelog = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="versions")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    workflow_version = Column(String(32))

    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    context = Column(JSONB)          # 全局执行上下文（所有 step 的中间结果）

    status = Column(String(32), nullable=False)   # pending | running | success | failed | cancelled
    error_message = Column(Text)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration_ms = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="runs")
    step_runs = relationship("StepRun", back_populates="workflow_run")


class StepRun(Base):
    __tablename__ = "step_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"))
    step_id = Column(String(128), nullable=False)   # 对应 DAG 中的 step.id
    node_name = Column(String(128))

    input_data = Column(JSONB)
    output_data = Column(JSONB)
    status = Column(String(32))     # pending | running | success | failed | skipped | retrying
    attempt = Column(Integer, default=1)
    error_message = Column(Text)

    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    latency_ms = Column(Integer)

    workflow_run = relationship("WorkflowRun", back_populates="step_runs")
```

---

## 四、DAG 执行引擎

### 4.1 执行引擎架构

```python
# workflow/executor.py
import asyncio
from typing import Any
from uuid import UUID


class WorkflowExecutor:
    """
    Workflow DAG 执行引擎

    执行策略：
    1. 拓扑排序确定执行顺序
    2. 没有依赖的 Step 立即执行
    3. 所有依赖满足的 Step 并行执行
    4. 任何 Step 失败根据 error_strategy 决定是否中止
    """

    def __init__(self, registry, runtime_dispatcher, db_session):
        self.registry = registry
        self.dispatcher = runtime_dispatcher
        self.db = db_session

    async def execute(
        self,
        workflow_run_id: UUID,
        dag_definition: dict,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """执行完整的 Workflow"""

        steps = {s["id"]: s for s in dag_definition["steps"]}
        error_strategy = dag_definition.get("error_strategy", "fail_fast")
        max_parallel = dag_definition.get("max_parallel_steps", 10)

        # 执行上下文，存储所有 Step 的输出
        context = {
            "input": input_data,
            "steps": {},
        }

        # 追踪各 Step 状态
        step_status: dict[str, str] = {sid: "pending" for sid in steps}
        pending_tasks: dict[str, asyncio.Task] = {}

        async def can_run(step_id: str) -> bool:
            step = steps[step_id]
            return all(
                step_status.get(dep) == "success"
                for dep in step.get("depends_on", [])
            )

        async def run_step(step: dict) -> tuple[str, dict]:
            step_id = step["id"]
            await self._update_step_status(workflow_run_id, step_id, "running")

            try:
                # 解析输入映射
                step_input = self._resolve_input_mapping(step["input_mapping"], context)

                # 获取 Node 信息
                node = await self.registry.get_node_by_name(step["node"])
                version_str = step.get("node_version", "latest")
                version = await self.registry.get_version(node.id, version_str if version_str != "latest" else None)

                # 执行 Node
                executor = self.dispatcher.get_executor(version.runtime_config["type"])
                output, latency_ms = await executor.execute(version.runtime_config, step_input)

                await self._update_step_result(workflow_run_id, step_id, "success", output, latency_ms)
                return step_id, output

            except Exception as e:
                await self._update_step_result(workflow_run_id, step_id, "failed", error=str(e))
                raise

        # 主调度循环
        semaphore = asyncio.Semaphore(max_parallel)

        async def run_with_semaphore(step):
            async with semaphore:
                return await run_step(step)

        while any(s == "pending" for s in step_status.values()):
            # 找出所有可以执行的 Step
            ready_steps = [
                sid for sid, status in step_status.items()
                if status == "pending" and await can_run(sid)
            ]

            if not ready_steps and not pending_tasks:
                # 死锁：没有可执行的 Step 且没有进行中的任务
                break

            # 启动所有 ready 的 Step
            for step_id in ready_steps:
                step_status[step_id] = "running"
                task = asyncio.create_task(run_with_semaphore(steps[step_id]))
                pending_tasks[step_id] = task

            # 等待任意一个任务完成
            done, _ = await asyncio.wait(
                pending_tasks.values(),
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                step_id = next(sid for sid, t in pending_tasks.items() if t == task)
                del pending_tasks[step_id]

                try:
                    _, output = task.result()
                    step_status[step_id] = "success"
                    context["steps"][step_id] = {"output": output, "status": "success"}
                except Exception as e:
                    step_status[step_id] = "failed"
                    context["steps"][step_id] = {"status": "failed", "error": str(e)}
                    if error_strategy == "fail_fast":
                        # 取消所有进行中的任务
                        for t in pending_tasks.values():
                            t.cancel()
                        raise RuntimeError(f"Step '{step_id}' failed: {e}")

        # 提取最终输出
        output_step = dag_definition.get("output_step")
        if output_step:
            return context["steps"].get(output_step, {}).get("output", {})
        return context

    def _resolve_input_mapping(
        self, mapping: dict[str, Any], context: dict
    ) -> dict[str, Any]:
        """
        解析 input_mapping，将 JSONPath 引用替换为实际值

        "$.input.transactions" → context["input"]["transactions"]
        "$.steps.step_a.output.result" → context["steps"]["step_a"]["output"]["result"]
        literal_value → literal_value
        """
        resolved = {}
        for key, value in mapping.items():
            if isinstance(value, str) and value.startswith("$."):
                resolved[key] = self._jsonpath_get(context, value)
            else:
                resolved[key] = value
        return resolved

    def _jsonpath_get(self, data: dict, path: str) -> Any:
        """简单 JSONPath 实现（仅支持点号路径）"""
        parts = path.lstrip("$.").split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
```

### 4.2 DAG 验证器

```python
# workflow/validator.py

class DAGValidator:
    """验证 Workflow DAG 定义的合法性"""

    def validate(self, dag_definition: dict) -> tuple[bool, list[str]]:
        errors = []
        steps = {s["id"]: s for s in dag_definition.get("steps", [])}

        # 1. 检查是否有 steps
        if not steps:
            errors.append("Workflow 必须包含至少一个 Step")

        # 2. 检查依赖引用有效
        for step_id, step in steps.items():
            for dep in step.get("depends_on", []):
                if dep not in steps:
                    errors.append(f"Step '{step_id}' 依赖不存在的 Step '{dep}'")

        # 3. 检查循环依赖（拓扑排序）
        if not errors:
            cycle = self._detect_cycle(steps)
            if cycle:
                errors.append(f"检测到循环依赖: {' → '.join(cycle)}")

        # 4. 检查 output_step 存在
        output_step = dag_definition.get("output_step")
        if output_step and output_step not in steps:
            errors.append(f"output_step '{output_step}' 在 steps 中不存在")

        return len(errors) == 0, errors

    def _detect_cycle(self, steps: dict) -> list[str] | None:
        """使用 DFS 检测环"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {sid: WHITE for sid in steps}
        path = []

        def dfs(node: str) -> bool:
            color[node] = GRAY
            path.append(node)
            for dep in steps[node].get("depends_on", []):
                if dep not in color:
                    continue
                if color[dep] == GRAY:
                    cycle_start = path.index(dep)
                    return path[cycle_start:]
                if color[dep] == WHITE:
                    result = dfs(dep)
                    if result:
                        return result
            path.pop()
            color[node] = BLACK
            return None

        for step_id in steps:
            if color[step_id] == WHITE:
                result = dfs(step_id)
                if result:
                    return result
        return None
```

---

## 五、Workflow API 设计

```python
# api/v1/workflows.py

# ===== Workflow CRUD =====
POST   /api/v1/workflows              # 创建 Workflow（含 DAG 定义）
GET    /api/v1/workflows              # 列出 Workflow
GET    /api/v1/workflows/{id}         # 获取详情
PATCH  /api/v1/workflows/{id}         # 更新
DELETE /api/v1/workflows/{id}         # 删除

# ===== 版本管理 =====
GET    /api/v1/workflows/{id}/versions
POST   /api/v1/workflows/{id}/versions

# ===== 执行 =====
POST   /api/v1/workflows/{id}/run     # 触发执行
GET    /api/v1/workflows/{id}/runs    # 历史执行列表
GET    /api/v1/workflows/{id}/runs/{run_id}     # 某次执行详情
DELETE /api/v1/workflows/{id}/runs/{run_id}     # 取消执行（如果还在运行）

# ===== 执行详情 =====
GET    /api/v1/runs/{run_id}/steps    # 获取所有 Step 的执行状态
GET    /api/v1/runs/{run_id}/logs     # 实时日志（SSE）
```

### 5.1 触发执行 API

```python
@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse, status_code=202)
async def trigger_workflow(
    workflow_id: UUID,
    payload: WorkflowRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    触发 Workflow 执行。

    - 立即返回 run_id（202 Accepted，异步执行）
    - 通过 GET /runs/{run_id} 轮询状态
    - 支持 SSE 实时日志流
    """
    # 创建 WorkflowRun 记录
    run = WorkflowRun(
        workflow_id=workflow_id,
        triggered_by=current_user.id,
        input_data=payload.input,
        status="pending",
    )
    db.add(run)
    await db.commit()

    # 后台异步执行
    background_tasks.add_task(
        execute_workflow_background,
        run_id=run.id,
        workflow_id=workflow_id,
        version=payload.version,
        input_data=payload.input,
    )

    return WorkflowRunResponse(
        run_id=run.id,
        status="pending",
        message="Workflow 已提交，正在异步执行",
    )
```

### 5.2 实时日志 SSE

```python
@router.get("/{run_id}/logs")
async def stream_run_logs(
    run_id: UUID,
    current_user = Depends(get_current_user),
):
    """
    实时获取 Workflow 执行日志（Server-Sent Events）

    客户端代码：
    const source = new EventSource('/api/v1/runs/{run_id}/logs');
    source.onmessage = (event) => console.log(JSON.parse(event.data));
    """
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        while True:
            logs = await get_new_logs(run_id)
            for log in logs:
                yield f"data: {json.dumps(log)}\n\n"

            run = await get_run_status(run_id)
            if run.status in ("success", "failed", "cancelled"):
                yield f"data: {json.dumps({'type': 'terminal', 'status': run.status})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
```

---

## 六、Workflow 可视化设计

NodeVault Dashboard 需要为 Workflow 提供可视化 DAG 编辑器。

### 6.1 前端技术选型

| 功能 | 技术 |
|------|------|
| DAG 可视化 | **React Flow** 或 **vue-flow** |
| 前端框架 | Vue 3 + Naive UI |
| 实时状态 | SSE / WebSocket |

### 6.2 DAG 编辑器 UI 规范

```
┌─────────────────────────────────────────────┐
│  Workflow: fund_risk_analysis_pipeline      │
├─────────────────────────────────────────────┤
│                                             │
│   [clean_data] ──→ [analyze_flow] ──┐       │
│        │                            ▼       │
│        └──────→ [detect_pool] ──→ [risk_score] → [report] │
│                                             │
└─────────────────────────────────────────────┘

图例:
  绿色节点 = 执行成功
  黄色节点 = 执行中
  红色节点 = 执行失败
  灰色节点 = 等待中
```

---

## 七、Workflow 条件逻辑（可选高级特性）

```json
{
  "id": "risk_alert",
  "node": "send_risk_alert",
  "depends_on": ["risk_score"],
  "condition": "$.steps.risk_score.output.score > 0.8",
  "description": "仅在风险评分超过0.8时才发送告警"
}
```

Condition 表达式支持：
- JSONPath 引用
- 比较运算符：`>`, `<`, `>=`, `<=`, `==`, `!=`
- 逻辑运算符：`&&`, `||`, `!`
- 内置函数：`len()`, `contains()`, `exists()`

---

## 八、Phase 4 交付检查清单

```
□ WorkflowVersion 数据库模型和迁移
□ WorkflowRun / StepRun 数据库模型
□ DAG 验证器（循环依赖、引用有效性）
□ DAG 执行引擎（并行、串行、失败策略）
□ Input Mapping JSONPath 解析器
□ Workflow CRUD API
□ 触发执行 API（异步，202 返回）
□ 执行状态查询 API
□ 实时日志 SSE 接口
□ Step 执行重试机制
□ 执行超时机制
□ DAG 可视化前端（基础版）
□ 条件执行支持（可选）
□ Workflow 导出为 JSON/YAML
□ 单元测试（DAG 验证器、输入映射解析）
□ 集成测试（完整 Workflow 执行）
□ Workflow 使用文档
```

---

> **上一步 ←** [Phase 3 - Skill 导出与 Agent 集成](./Phase3-Skill导出与Agent集成.md)
> **下一步 →** [Phase 5 - 企业级治理](./Phase5-企业级治理.md)
