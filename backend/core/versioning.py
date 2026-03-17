from typing import Any


class VersionCompatibilityChecker:
    """检查新版本的 Schema 变更是否向后兼容"""

    def check_compatibility(
        self,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        检查 new_schema 是否与 old_schema 向后兼容。
        返回: (is_compatible, list_of_issues)  issues 包含 breaking_changes 和 warnings
        """
        breaking_changes: list[str] = []
        warnings: list[str] = []

        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))
        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})

        # Breaking: 新增必填字段
        new_required_fields = new_required - old_required
        for field in new_required_fields:
            if field not in old_props:
                breaking_changes.append(
                    f"BREAKING: 新增了必填字段 '{field}'，旧版本调用者将无法满足要求"
                )

        # Breaking: 删除已有字段
        removed_fields = set(old_props.keys()) - set(new_props.keys())
        for field in removed_fields:
            breaking_changes.append(
                f"BREAKING: 删除了已有字段 '{field}'，可能导致旧版本调用者的输出处理失效"
            )

        # Warning: 字段类型变更
        for field in set(old_props.keys()) & set(new_props.keys()):
            old_type = old_props[field].get("type")
            new_type = new_props[field].get("type")
            if old_type != new_type:
                warnings.append(
                    f"WARNING: 字段 '{field}' 类型从 {old_type} 变更为 {new_type}"
                )

        is_compatible = len(breaking_changes) == 0
        return is_compatible, breaking_changes + warnings

    def suggest_version_bump(
        self,
        current_version: str,
        is_compatible: bool,
        has_new_features: bool = False,
    ) -> str:
        """根据兼容性结果建议下一个语义化版本号"""
        parts = current_version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        if not is_compatible:
            return f"{major + 1}.0.0"
        if has_new_features:
            return f"{major}.{minor + 1}.0"
        return f"{major}.{minor}.{patch + 1}"
