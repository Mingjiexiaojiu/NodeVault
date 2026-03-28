"""phase14_rename_namespace_to_department

- Rename table: namespaces -> departments
- Rename table: namespace_members -> department_members
- Rename column: department_members.namespace_id -> department_id
- Rename column: nodes.namespace_id -> department_id
- Rename column: skills.namespace_id -> department_id
- Drop column: users.department (text field, replaced by department_members relation)
- Rename all related FK constraints, unique constraints, and indexes

Revision ID: a2b3c4d5e6f7
Revises: d0e1f2a3b4c5
Create Date: 2026-03-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "a2b3c4d5e6f7"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Step 1: Drop FK constraints referencing namespaces / namespace_members ──
    op.drop_constraint("namespaces_owner_id_fkey", "namespaces", type_="foreignkey")
    op.drop_constraint("namespace_members_namespace_id_fkey", "namespace_members", type_="foreignkey")
    op.drop_constraint("namespace_members_user_id_fkey", "namespace_members", type_="foreignkey")
    op.drop_constraint("nodes_namespace_id_fkey", "nodes", type_="foreignkey")
    op.drop_constraint("skills_namespace_id_fkey", "skills", type_="foreignkey")

    # ── Step 2: Drop unique constraints that need to be recreated with new names ──
    op.drop_constraint("uq_namespace_member", "namespace_members", type_="unique")
    op.drop_constraint("uq_node_name_namespace", "nodes", type_="unique")
    op.drop_constraint("uq_skill_name_namespace", "skills", type_="unique")

    # ── Step 3: Rename tables ──
    op.rename_table("namespaces", "departments")
    op.rename_table("namespace_members", "department_members")

    # ── Step 4: Rename columns ──
    op.alter_column("department_members", "namespace_id", new_column_name="department_id")
    op.alter_column("nodes", "namespace_id", new_column_name="department_id")
    op.alter_column("skills", "namespace_id", new_column_name="department_id")

    # ── Step 5: Drop users.department text column ──
    op.drop_column("users", "department")

    # ── Step 6: Re-add FK constraints with new names ──
    op.create_foreign_key(
        "departments_owner_id_fkey", "departments", "users",
        ["owner_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "department_members_department_id_fkey", "department_members", "departments",
        ["department_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "department_members_user_id_fkey", "department_members", "users",
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "nodes_department_id_fkey", "nodes", "departments",
        ["department_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "skills_department_id_fkey", "skills", "departments",
        ["department_id"], ["id"], ondelete="CASCADE"
    )

    # ── Step 7: Re-add unique constraints with new names ──
    op.create_unique_constraint("uq_department_member", "department_members", ["department_id", "user_id"])
    op.create_unique_constraint("uq_node_name_department", "nodes", ["name", "department_id"])
    op.create_unique_constraint("uq_skill_name_department", "skills", ["name", "department_id"])

    # ── Step 8: Rename indexes ──
    op.execute("ALTER INDEX ix_namespace_members_namespace_id RENAME TO ix_department_members_department_id")
    op.execute("ALTER INDEX ix_namespace_members_user_id RENAME TO ix_department_members_user_id")
    op.execute("ALTER INDEX ix_namespaces_slug RENAME TO ix_departments_slug")
    op.execute("ALTER INDEX ix_skills_namespace_id RENAME TO ix_skills_department_id")


def downgrade() -> None:
    # ── Reverse Step 8: Rename indexes back ──
    op.execute("ALTER INDEX ix_department_members_department_id RENAME TO ix_namespace_members_namespace_id")
    op.execute("ALTER INDEX ix_department_members_user_id RENAME TO ix_namespace_members_user_id")
    op.execute("ALTER INDEX ix_departments_slug RENAME TO ix_namespaces_slug")
    op.execute("ALTER INDEX ix_skills_department_id RENAME TO ix_skills_namespace_id")

    # ── Reverse Step 7: Drop new unique constraints ──
    op.drop_constraint("uq_department_member", "department_members", type_="unique")
    op.drop_constraint("uq_node_name_department", "nodes", type_="unique")
    op.drop_constraint("uq_skill_name_department", "skills", type_="unique")

    # ── Reverse Step 6: Drop new FK constraints ──
    op.drop_constraint("departments_owner_id_fkey", "departments", type_="foreignkey")
    op.drop_constraint("department_members_department_id_fkey", "department_members", type_="foreignkey")
    op.drop_constraint("department_members_user_id_fkey", "department_members", type_="foreignkey")
    op.drop_constraint("nodes_department_id_fkey", "nodes", type_="foreignkey")
    op.drop_constraint("skills_department_id_fkey", "skills", type_="foreignkey")

    # ── Reverse Step 5: Restore users.department column ──
    op.add_column("users", sa.Column("department", sa.String(128), nullable=True))

    # ── Reverse Step 4: Rename columns back ──
    op.alter_column("department_members", "department_id", new_column_name="namespace_id")
    op.alter_column("nodes", "department_id", new_column_name="namespace_id")
    op.alter_column("skills", "department_id", new_column_name="namespace_id")

    # ── Reverse Step 3: Rename tables back ──
    op.rename_table("department_members", "namespace_members")
    op.rename_table("departments", "namespaces")

    # ── Reverse Step 2: Re-add old unique constraints ──
    op.create_unique_constraint("uq_namespace_member", "namespace_members", ["namespace_id", "user_id"])
    op.create_unique_constraint("uq_node_name_namespace", "nodes", ["name", "namespace_id"])
    op.create_unique_constraint("uq_skill_name_namespace", "skills", ["name", "namespace_id"])

    # ── Reverse Step 1: Re-add old FK constraints ──
    op.create_foreign_key(
        "namespaces_owner_id_fkey", "namespaces", "users",
        ["owner_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "namespace_members_namespace_id_fkey", "namespace_members", "namespaces",
        ["namespace_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "namespace_members_user_id_fkey", "namespace_members", "users",
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "nodes_namespace_id_fkey", "nodes", "namespaces",
        ["namespace_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "skills_namespace_id_fkey", "skills", "namespaces",
        ["namespace_id"], ["id"], ondelete="CASCADE"
    )
