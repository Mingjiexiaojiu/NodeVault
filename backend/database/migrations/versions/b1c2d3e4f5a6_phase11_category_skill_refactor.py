"""phase11_category_skill_refactor

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-03-19 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default categories matching the old NodeType enum
DEFAULT_CATEGORIES = [
    {"name": "data_cleaning", "display_name": "数据清洗", "icon": "broom", "sort_order": 0},
    {"name": "analysis", "display_name": "数据分析", "icon": "chart-bar", "sort_order": 1},
    {"name": "risk", "display_name": "风控", "icon": "shield", "sort_order": 2},
    {"name": "nlp", "display_name": "自然语言处理", "icon": "message-square", "sort_order": 3},
    {"name": "vision", "display_name": "计算机视觉", "icon": "eye", "sort_order": 4},
    {"name": "ml", "display_name": "机器学习", "icon": "cpu", "sort_order": 5},
    {"name": "tool", "display_name": "工具", "icon": "wrench", "sort_order": 6},
    {"name": "utility", "display_name": "通用", "icon": "box", "sort_order": 7},
]


def upgrade() -> None:
    # 1. Create categories table
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("icon", sa.String(64), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 2. Seed default categories
    categories_table = sa.table(
        "categories",
        sa.column("name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("icon", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_default", sa.Boolean),
    )
    op.bulk_insert(categories_table, [
        {**cat, "is_default": True} for cat in DEFAULT_CATEGORIES
    ])

    # 3. Create skill_nodes M2M table
    op.create_table(
        "skill_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("usage_hint", sa.String(500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("skill_id", "node_id", name="uq_skill_node"),
    )

    # 4. Add is_system to skills
    op.add_column("skills", sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"))

    # 5. Add category_id to nodes (nullable initially for data migration)
    op.add_column("nodes", sa.Column(
        "category_id",
        postgresql.UUID(as_uuid=True),
        nullable=True,
    ))

    # 6. Data migration: map old type values to category_id
    op.execute("""
        UPDATE nodes
        SET category_id = c.id
        FROM categories c
        WHERE nodes.type = c.name
    """)
    # For any nodes with type not matching a category, assign 'tool' as fallback
    op.execute("""
        UPDATE nodes
        SET category_id = (SELECT id FROM categories WHERE name = 'tool')
        WHERE category_id IS NULL
    """)

    # 7. Make category_id NOT NULL and add FK
    op.alter_column("nodes", "category_id", nullable=False)
    op.create_foreign_key("fk_nodes_category_id", "nodes", "categories", ["category_id"], ["id"])
    op.create_index("ix_nodes_category_id", "nodes", ["category_id"])

    # 8. Migrate skill_id + usage_hint from nodes to skill_nodes
    op.execute("""
        INSERT INTO skill_nodes (skill_id, node_id, usage_hint)
        SELECT skill_id, id, usage_hint
        FROM nodes
        WHERE skill_id IS NOT NULL
    """)

    # 9. Create system Skills for each default category
    # Using raw SQL since we need to reference both categories and skills tables
    op.execute("""
        INSERT INTO skills (id, name, display_name, description, namespace_id, owner_id, status, is_system, is_stale, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            c.name || '-collection',
            c.display_name || '技能集',
            '系统自动创建的' || c.display_name || '分类技能集',
            (SELECT id FROM namespaces LIMIT 1),
            (SELECT id FROM users WHERE role = 0 LIMIT 1),
            'active',
            true,
            false,
            now(),
            now()
        FROM categories c
        WHERE c.is_default = true
        AND EXISTS (SELECT 1 FROM namespaces LIMIT 1)
        AND EXISTS (SELECT 1 FROM users WHERE role = 0 LIMIT 1)
    """)

    # 10. Drop old columns from nodes
    op.drop_constraint("nodes_skill_id_fkey", "nodes", type_="foreignkey")
    op.drop_index("ix_nodes_skill_id", table_name="nodes")
    op.drop_index("ix_nodes_type", table_name="nodes")
    op.drop_index("ix_nodes_category", table_name="nodes")
    op.drop_column("nodes", "type")
    op.drop_column("nodes", "category")
    op.drop_column("nodes", "skill_id")
    op.drop_column("nodes", "usage_hint")


def downgrade() -> None:
    # 1. Re-add old columns to nodes
    op.add_column("nodes", sa.Column("type", sa.String(64), nullable=True))
    op.add_column("nodes", sa.Column("category", sa.String(128), nullable=True))
    op.add_column("nodes", sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("nodes", sa.Column("usage_hint", sa.String(500), nullable=True))

    # 2. Restore data from categories back to type
    op.execute("""
        UPDATE nodes
        SET type = c.name
        FROM categories c
        WHERE nodes.category_id = c.id
    """)
    op.alter_column("nodes", "type", nullable=False)

    # 3. Restore skill_id + usage_hint from skill_nodes (take first skill per node)
    op.execute("""
        UPDATE nodes
        SET skill_id = sn.skill_id, usage_hint = sn.usage_hint
        FROM (
            SELECT DISTINCT ON (node_id) node_id, skill_id, usage_hint
            FROM skill_nodes
            ORDER BY node_id, created_at ASC
        ) sn
        WHERE nodes.id = sn.node_id
    """)

    # 4. Re-create indexes and FK for old columns
    op.create_index("ix_nodes_type", "nodes", ["type"])
    op.create_index("ix_nodes_category", "nodes", ["category"])
    op.create_index("ix_nodes_skill_id", "nodes", ["skill_id"])
    op.create_foreign_key("nodes_skill_id_fkey", "nodes", "skills", ["skill_id"], ["id"], ondelete="SET NULL")

    # 5. Drop new column and constraints
    op.drop_index("ix_nodes_category_id", table_name="nodes")
    op.drop_constraint("fk_nodes_category_id", "nodes", type_="foreignkey")
    op.drop_column("nodes", "category_id")

    # 6. Remove is_system from skills (and delete system skills)
    op.execute("DELETE FROM skills WHERE is_system = true")
    op.drop_column("skills", "is_system")

    # 7. Drop tables
    op.drop_table("skill_nodes")
    op.drop_table("categories")
