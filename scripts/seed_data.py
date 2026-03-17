"""
种子数据脚本 — 创建测试用户、节点、版本、标签和调用日志

用法：
    conda run -n NodeVault python scripts/seed_data.py

功能：
    - 创建 2 个测试账号（demo / alice）
    - 为每个账号创建命名空间（自动）
    - 创建 8 个不同类型的 Node，含标签和版本
    - 为每个 Node 写入若干模拟调用日志
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 确保能 import backend 包
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.auth.jwt import get_password_hash
from backend.core.config import settings
from backend.database.base import Base
from backend.models.namespace import Namespace
from backend.models.node import Node, NodeInvocationLog, NodeTag, NodeVersion
from backend.models.user import User

# ─── 种子数据定义 ────────────────────────────────────────────────────────────

USERS = [
    {"email": "demo@nodevault.dev", "username": "demo", "password": "demo1234"},
    {"email": "alice@nodevault.dev", "username": "alice", "password": "alice1234"},
]

# (owner_username, name, display_name, type, status, category, description, tags, versions)
NODES: list[dict] = [
    {
        "owner": "demo",
        "name": "text_sentiment",
        "display_name": "文本情感分析",
        "type": "nlp",
        "status": "active",
        "visibility": "public",
        "category": "nlp",
        "description": "对输入文本进行情感极性分析，返回正向/负向/中性及置信度。",
        "tags": ["nlp", "sentiment", "text"],
        "versions": [
            {
                "version": "1.0.0",
                "changelog": "初始版本，支持中英文双语",
                "is_default": False,
                "runtime_config": {"type": "http", "endpoint": "http://ml-service/sentiment/v1", "method": "POST", "timeout": 10},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "待分析文本"},
                        "lang": {"type": "string", "enum": ["zh", "en"], "description": "语言代码"}
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                        "score": {"type": "number"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 145},
                    {"status": "success", "latency_ms": 132},
                    {"status": "success", "latency_ms": 178},
                    {"status": "failure", "latency_ms": 5001, "error": "upstream timeout"},
                ],
            },
            {
                "version": "1.1.0",
                "changelog": "提升中文准确率，增加 neutral 置信度阈值参数",
                "is_default": True,
                "runtime_config": {"type": "http", "endpoint": "http://ml-service/sentiment/v2", "method": "POST", "timeout": 10},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "待分析文本"},
                        "lang": {"type": "string", "enum": ["zh", "en"]},
                        "threshold": {"type": "number", "default": 0.5}
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "score": {"type": "number"},
                        "details": {"type": "object"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 98},
                    {"status": "success", "latency_ms": 103},
                    {"status": "success", "latency_ms": 87},
                    {"status": "success", "latency_ms": 115},
                    {"status": "success", "latency_ms": 109},
                    {"status": "timeout", "latency_ms": 10000, "error": "execution timed out"},
                ],
            },
        ],
    },
    {
        "owner": "demo",
        "name": "invoice_ocr",
        "display_name": "发票 OCR 识别",
        "type": "vision",
        "status": "active",
        "category": "finance",
        "description": "识别增值税专用发票、普通发票等图片，提取发票号、金额、税率等结构化字段。",
        "tags": ["ocr", "finance", "vision", "invoice"],
        "versions": [
            {
                "version": "2.0.1",
                "changelog": "修复部分模糊图片漏识别问题",
                "is_default": True,
                "runtime_config": {"type": "http", "endpoint": "http://ocr-service/invoice", "method": "POST", "timeout": 30},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "image_base64": {"type": "string", "description": "Base64 编码的发票图片"},
                        "invoice_type": {"type": "string", "enum": ["vat_special", "vat_normal", "receipt"]}
                    },
                    "required": ["image_base64"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "invoice_code": {"type": "string"},
                        "invoice_number": {"type": "string"},
                        "amount": {"type": "number"},
                        "tax_rate": {"type": "number"},
                        "date": {"type": "string"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 450},
                    {"status": "success", "latency_ms": 512},
                    {"status": "success", "latency_ms": 389},
                    {"status": "success", "latency_ms": 601},
                    {"status": "success", "latency_ms": 477},
                    {"status": "success", "latency_ms": 498},
                    {"status": "failure", "latency_ms": 230, "error": "image too blurry"},
                ],
            }
        ],
    },
    {
        "owner": "demo",
        "name": "credit_risk_score",
        "display_name": "信贷风险评分",
        "type": "risk",
        "status": "active",
        "category": "risk",
        "description": "根据用户基本信息和历史行为计算信贷风险评分（0-1000），并给出审批建议。",
        "tags": ["risk", "credit", "finance", "ml"],
        "versions": [
            {
                "version": "3.2.0",
                "changelog": "引入 XGBoost 模型，提升 AUC 至 0.89",
                "is_default": True,
                "runtime_config": {"type": "http", "endpoint": "http://risk-engine/credit/score", "method": "POST", "timeout": 5},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer"},
                        "income": {"type": "number", "description": "月收入（元）"},
                        "debt_ratio": {"type": "number", "description": "负债比"},
                        "history_months": {"type": "integer", "description": "信用历史月数"},
                        "overdue_count": {"type": "integer", "description": "历史逾期次数"}
                    },
                    "required": ["age", "income", "debt_ratio"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "description": "0-1000 风险评分"},
                        "level": {"type": "string", "enum": ["low", "medium", "high"]},
                        "suggestion": {"type": "string"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 56},
                    {"status": "success", "latency_ms": 48},
                    {"status": "success", "latency_ms": 61},
                    {"status": "success", "latency_ms": 52},
                    {"status": "success", "latency_ms": 55},
                    {"status": "success", "latency_ms": 49},
                    {"status": "success", "latency_ms": 58},
                    {"status": "success", "latency_ms": 53},
                ],
            }
        ],
    },
    {
        "owner": "demo",
        "name": "transaction_anomaly",
        "display_name": "交易异常检测",
        "type": "risk",
        "status": "active",
        "category": "risk",
        "description": "实时检测单笔交易是否存在欺诈风险，返回风险等级和触发规则列表。",
        "tags": ["risk", "fraud", "realtime"],
        "versions": [
            {
                "version": "1.0.0",
                "changelog": "上线基础规则引擎",
                "is_default": False,
                "runtime_config": {"type": "http", "endpoint": "http://fraud-service/detect/v1", "method": "POST", "timeout": 3},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "merchant_id": {"type": "string"},
                        "user_id": {"type": "string"},
                        "timestamp": {"type": "string"}
                    },
                    "required": ["amount", "user_id"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "is_anomaly": {"type": "boolean"},
                        "risk_level": {"type": "string"},
                        "rules_triggered": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 23},
                    {"status": "success", "latency_ms": 19},
                ],
            },
            {
                "version": "2.0.0",
                "changelog": "加入机器学习模型，召回率提升 35%",
                "is_default": True,
                "runtime_config": {"type": "http", "endpoint": "http://fraud-service/detect/v2", "method": "POST", "timeout": 3},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "merchant_id": {"type": "string"},
                        "user_id": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "device_fingerprint": {"type": "string"}
                    },
                    "required": ["amount", "user_id"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "is_anomaly": {"type": "boolean"},
                        "risk_score": {"type": "number"},
                        "risk_level": {"type": "string"},
                        "rules_triggered": {"type": "array", "items": {"type": "string"}},
                        "model_confidence": {"type": "number"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 31},
                    {"status": "success", "latency_ms": 28},
                    {"status": "success", "latency_ms": 35},
                    {"status": "success", "latency_ms": 27},
                    {"status": "success", "latency_ms": 42},
                ],
            },
        ],
    },
    {
        "owner": "alice",
        "name": "data_dedup",
        "display_name": "数据去重清洗",
        "type": "data_cleaning",
        "status": "active",
        "category": "data",
        "description": "对表格数据进行重复行检测与去除，支持模糊匹配和精确匹配两种模式。",
        "tags": ["data", "cleaning", "dedup"],
        "versions": [
            {
                "version": "1.2.0",
                "changelog": "支持模糊去重和多列联合主键",
                "is_default": True,
                "runtime_config": {"type": "http", "endpoint": "http://data-pipe/dedup", "method": "POST", "timeout": 60},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "array", "items": {"type": "object"}},
                        "key_columns": {"type": "array", "items": {"type": "string"}},
                        "mode": {"type": "string", "enum": ["exact", "fuzzy"], "default": "exact"}
                    },
                    "required": ["data", "key_columns"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "cleaned_data": {"type": "array"},
                        "removed_count": {"type": "integer"},
                        "total_input": {"type": "integer"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 1230},
                    {"status": "success", "latency_ms": 876},
                    {"status": "success", "latency_ms": 2100},
                ],
            }
        ],
    },
    {
        "owner": "alice",
        "name": "translate_text",
        "display_name": "多语言文本翻译",
        "type": "nlp",
        "status": "active",
        "category": "nlp",
        "description": "支持 50+ 语言互译，基于大语言模型，针对金融、法律领域优化。",
        "tags": ["nlp", "translation", "multilingual"],
        "versions": [
            {
                "version": "1.0.0",
                "changelog": "初始版本，支持中英日韩",
                "is_default": False,
                "runtime_config": {"type": "http", "endpoint": "http://llm-gateway/translate/v1", "method": "POST", "timeout": 20},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "source_lang": {"type": "string", "default": "auto"},
                        "target_lang": {"type": "string"}
                    },
                    "required": ["text", "target_lang"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "translated_text": {"type": "string"},
                        "detected_source": {"type": "string"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 650},
                    {"status": "success", "latency_ms": 720},
                ],
            },
            {
                "version": "2.0.0",
                "changelog": "升级至 GPT-4 后端，支持 50+ 语言，金融术语词典加强",
                "is_default": True,
                "runtime_config": {"type": "http", "endpoint": "http://llm-gateway/translate/v2", "method": "POST", "timeout": 20},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "source_lang": {"type": "string", "default": "auto"},
                        "target_lang": {"type": "string"},
                        "domain": {"type": "string", "enum": ["general", "finance", "legal", "medical"], "default": "general"}
                    },
                    "required": ["text", "target_lang"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "translated_text": {"type": "string"},
                        "detected_source": {"type": "string"},
                        "confidence": {"type": "number"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 890},
                    {"status": "success", "latency_ms": 710},
                    {"status": "success", "latency_ms": 830},
                    {"status": "success", "latency_ms": 760},
                ],
            },
        ],
    },
    {
        "owner": "alice",
        "name": "pdf_extractor",
        "display_name": "PDF 结构提取",
        "type": "tool",
        "status": "draft",
        "category": "document",
        "description": "从 PDF 文件中提取文本、表格、图片，输出结构化 JSON，支持中文版面分析。",
        "tags": ["tool", "pdf", "document", "ocr"],
        "versions": [
            {
                "version": "0.1.0",
                "changelog": "Alpha 版本，基础文本提取",
                "is_default": True,
                "runtime_config": {"type": "http", "endpoint": "http://doc-service/pdf/extract", "method": "POST", "timeout": 120},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pdf_base64": {"type": "string"},
                        "extract_tables": {"type": "boolean", "default": True},
                        "extract_images": {"type": "boolean", "default": False}
                    },
                    "required": ["pdf_base64"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "tables": {"type": "array"},
                        "page_count": {"type": "integer"}
                    }
                },
                "invocations": [],
            }
        ],
    },
    {
        "owner": "demo",
        "name": "address_parser",
        "display_name": "地址解析标准化",
        "type": "utility",
        "status": "active",
        "category": "data",
        "description": "将非结构化中文地址字符串解析为省/市/区/街道/门牌号等标准字段。",
        "tags": ["utility", "address", "nlp", "china"],
        "versions": [
            {
                "version": "1.3.2",
                "changelog": "修复海南自贸港地址解析错误",
                "is_default": True,
                "runtime_config": {"type": "http", "endpoint": "http://geo-service/address/parse", "method": "POST", "timeout": 5},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "原始地址字符串"},
                        "fuzzy": {"type": "boolean", "default": False}
                    },
                    "required": ["address"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "province": {"type": "string"},
                        "city": {"type": "string"},
                        "district": {"type": "string"},
                        "street": {"type": "string"},
                        "number": {"type": "string"},
                        "raw": {"type": "string"}
                    }
                },
                "invocations": [
                    {"status": "success", "latency_ms": 18},
                    {"status": "success", "latency_ms": 15},
                    {"status": "success", "latency_ms": 22},
                    {"status": "success", "latency_ms": 17},
                    {"status": "success", "latency_ms": 19},
                    {"status": "success", "latency_ms": 14},
                    {"status": "success", "latency_ms": 21},
                    {"status": "success", "latency_ms": 16},
                    {"status": "success", "latency_ms": 25},
                    {"status": "failure", "latency_ms": 1, "error": "address too short"},
                ],
            }
        ],
    },
]


# ─── 脚本逻辑 ────────────────────────────────────────────────────────────────

engine = create_async_engine(settings.database_url, echo=False)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_or_create_user(db: AsyncSession, u: dict) -> User:
    result = await db.execute(select(User).where(User.email == u["email"]))
    existing = result.scalar_one_or_none()
    if existing:
        print(f"  ✓ 已存在用户: {u['username']}")
        return existing

    user = User(
        email=u["email"],
        username=u["username"],
        hashed_password=get_password_hash(u["password"]),
    )
    db.add(user)
    await db.flush()

    ns = Namespace(slug=u["username"], display_name=u["username"], owner_id=user.id)
    db.add(ns)
    await db.flush()

    print(f"  ✓ 创建用户: {u['username']} (namespace: {u['username']})")
    return user


async def seed(db: AsyncSession) -> None:
    # 1. 用户
    print("\n── 用户 ──────────────────────────────")
    users: dict[str, User] = {}
    namespaces: dict[str, Namespace] = {}
    for u in USERS:
        user = await get_or_create_user(db, u)
        users[u["username"]] = user

        ns_result = await db.execute(select(Namespace).where(Namespace.slug == u["username"]))
        ns = ns_result.scalar_one_or_none()
        if ns:
            namespaces[u["username"]] = ns

    # 2. 节点
    print("\n── 节点 ──────────────────────────────")
    for node_def in NODES:
        owner = users[node_def["owner"]]
        ns = namespaces.get(node_def["owner"])
        if ns is None:
            print(f"  ✗ 找不到命名空间: {node_def['owner']}")
            continue

        # 检查是否已存在
        existing_node = await db.execute(
            select(Node).where(Node.name == node_def["name"], Node.namespace_id == ns.id)
        )
        if existing_node.scalar_one_or_none():
            print(f"  ✓ 已存在节点: {node_def['name']} (跳过)")
            continue

        node = Node(
            name=node_def["name"],
            display_name=node_def["display_name"],
            description=node_def["description"],
            type=node_def["type"],
            status=node_def["status"],
            category=node_def["category"],
            namespace_id=ns.id,
            owner_id=owner.id,
            invocation_count=sum(len(v["invocations"]) for v in node_def["versions"]),
        )
        db.add(node)
        await db.flush()

        # 标签
        for tag in node_def["tags"]:
            db.add(NodeTag(node_id=node.id, tag=tag))

        # 版本 + 调用日志
        total_logs = 0
        for vdef in node_def["versions"]:
            version = NodeVersion(
                node_id=node.id,
                version=vdef["version"],
                changelog=vdef["changelog"],
                is_default=vdef["is_default"],
                is_deprecated=False,
                runtime_config=vdef["runtime_config"],
                input_schema=vdef["input_schema"],
                output_schema=vdef["output_schema"],
                created_by=owner.id,
            )
            db.add(version)
            await db.flush()

            for i, inv in enumerate(vdef["invocations"]):
                created_at = datetime.utcnow() - timedelta(
                    days=random.randint(0, 29),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )
                log = NodeInvocationLog(
                    node_id=node.id,
                    version=vdef["version"],
                    invoked_by=owner.id,
                    input_data={"_seed": True},
                    output_data={"_seed": True} if inv["status"] == "success" else None,
                    status=inv["status"],
                    latency_ms=inv["latency_ms"],
                    error_message=inv.get("error"),
                    created_at=created_at,
                )
                db.add(log)
                total_logs += 1

        tags_str = ", ".join(node_def["tags"])
        print(f"  ✓ 创建节点: {node_def['name']} [{node_def['type']}] | {len(node_def['versions'])} 个版本 | {total_logs} 条日志 | 标签: {tags_str}")

    await db.commit()
    print("\n✅ 种子数据写入完成！\n")
    print("测试账号：")
    for u in USERS:
        print(f"  邮箱: {u['email']}  密码: {u['password']}")


async def main() -> None:
    async with session_factory() as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
