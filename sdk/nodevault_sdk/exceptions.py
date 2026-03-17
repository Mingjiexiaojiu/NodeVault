class NodeVaultError(Exception):
    """NodeVault SDK 基础异常"""


class AuthError(NodeVaultError):
    """认证失败（401）"""


class NodeNotFoundError(NodeVaultError):
    """Node 不存在（404）"""
