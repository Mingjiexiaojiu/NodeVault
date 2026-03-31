"""Phase 17: UX naming refactor — organizations, department restructure, category simplification, skill display_name required.

- Create organizations table
- Migrate departments: add org_id, rename display_name → team_name, drop slug
- Categories: drop name column, add UNIQUE on display_name
- Skills: display_name NOT NULL

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "h2i3j4k5l6m7"
down_revision = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"])

    # 2. Populate organizations from existing departments.slug (deduplicated)
    op.execute("""
        INSERT INTO organizations (id, name, created_at)
        SELECT gen_random_uuid(), slug, now()
        FROM departments
        GROUP BY slug
    """)

    # 3. Add org_id column to departments (nullable first for backfill)
    op.add_column("departments", sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True))

    # 4. Backfill org_id from slug → organizations.name
    op.execute("""
        UPDATE departments
        SET org_id = o.id
        FROM organizations o
        WHERE departments.slug = o.name
    """)

    # 5. Make org_id NOT NULL
    op.alter_column("departments", "org_id", nullable=False)

    # 6. Add FK constraint
    op.create_foreign_key(
        "fk_departments_org_id",
        "departments",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_departments_org_id", "departments", ["org_id"])

    # 7. Rename display_name → team_name
    op.alter_column("departments", "display_name", new_column_name="team_name")

    # 8. Backfill NULL team_name with slug value
    op.execute("""
        UPDATE departments SET team_name = slug WHERE team_name IS NULL
    """)

    # 9. Make team_name NOT NULL
    op.alter_column("departments", "team_name", nullable=False)

    # 10. Drop slug column and its index/unique constraint
    op.drop_index("ix_departments_slug", table_name="departments")
    op.drop_column("departments", "slug")

    # 11. Add UNIQUE(org_id, team_name) constraint
    op.create_unique_constraint("uq_org_team_name", "departments", ["org_id", "team_name"])

    # ── Categories ──

    # 12. Add UNIQUE constraint on categories.display_name
    op.create_unique_constraint("uq_category_display_name", "categories", ["display_name"])

    # 13. Drop name column and its index/unique constraint
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_constraint("categories_name_key", "categories", type_="unique")
    op.drop_column("categories", "name")

    # ── Skills ──

    # 14. Backfill NULL display_name with name value
    op.execute("""
        UPDATE skills SET display_name = name WHERE display_name IS NULL
    """)

    # 15. Make display_name NOT NULL
    op.alter_column("skills", "display_name", nullable=False)


def downgrade() -> None:
    # ── Skills: revert display_name to nullable ──
    op.alter_column("skills", "display_name", nullable=True)

    # ── Categories: restore name column ──
    op.add_column("categories", sa.Column("name", sa.String(64), nullable=True))
    # Backfill name from display_name (generate snake_case approximation)
    op.execute("""
        UPDATE categories SET name = lower(replace(display_name, ' ', '_'))
    """)
    op.alter_column("categories", "name", nullable=False)
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_unique_constraint("categories_name_key", "categories", ["name"])
    op.drop_constraint("uq_category_display_name", "categories", type_="unique")

    # ── Departments: restore slug, rename team_name → display_name, drop org_id ──
    op.drop_constraint("uq_org_team_name", "departments", type_="unique")
    op.add_column("departments", sa.Column("slug", sa.String(64), nullable=True))

    # Backfill slug from organization name
    op.execute("""
        UPDATE departments
        SET slug = o.name
        FROM organizations o
        WHERE departments.org_id = o.id
    """)
    op.alter_column("departments", "slug", nullable=False)
    op.create_index("ix_departments_slug", "departments", ["slug"])
    op.create_unique_constraint("departments_slug_key", "departments", ["slug"])

    # Rename team_name → display_name
    op.alter_column("departments", "team_name", new_column_name="display_name")
    op.alter_column("departments", "display_name", nullable=True)

    # Drop org_id FK and column
    op.drop_constraint("fk_departments_org_id", "departments", type_="foreignkey")
    op.drop_index("ix_departments_org_id", table_name="departments")
    op.drop_column("departments", "org_id")

    # Drop organizations table
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("organizations")
