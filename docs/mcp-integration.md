# MCP Server 集成指南

NodeVault 内置 Model Context Protocol (MCP) Server，让 Claude Desktop、VS Code Copilot 等支持 MCP 的客户端直接访问所有注册 Node。

## 架构

```
MCP 客户端 (Claude Desktop / VS Code Copilot / 自定义客户端)
      │  MCP over SSE
      ▼
GET http://<nodevault-host>/mcp/sse
      │
NodeVault MCP Server (FastMCP SSE transport)
      │
      ├── list_nodevault_nodes() → 返回所有 active Node 描述
      └── invoke_nodevault_node(name, arguments_json) → 执行 Node 并返回结果
```

## Claude Desktop 配置

编辑 Claude Desktop 配置文件（macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`，Windows: `%APPDATA%\Claude\claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "nodevault": {
      "url": "http://your-nodevault-host/mcp/sse",
      "headers": {
        "Authorization": "Bearer <your-api-token>"
      }
    }
  }
}
```

重启 Claude Desktop 后，Claude 会自动发现并调用所有 active NodeVault Node。

## VS Code Copilot 配置

在 VS Code settings（`.vscode/settings.json` 或用户设置）中添加：

```json
{
  "mcp": {
    "servers": {
      "nodevault": {
        "type": "sse",
        "url": "http://your-nodevault-host/mcp/sse",
        "headers": {
          "Authorization": "Bearer <your-api-token>"
        }
      }
    }
  }
}
```

## 可用工具

MCP 服务器暴露两个工具：

### `list_nodevault_nodes`
列出所有 active Node 的 OpenAI tool 格式描述。

参数：
- `tags`（可选）：逗号分隔的标签过滤，如 `"finance,risk"`
- `type`（可选）：Node 类型过滤，如 `"tool"`

### `invoke_nodevault_node`
按名称执行 Node。

参数：
- `name`：Node 名称（如 `"detect_fund_pool"`）
- `arguments_json`：JSON 字符串格式的输入参数（如 `'{"transactions": [...]}'`）

## 获取 API Token

```bash
curl -X POST http://your-nodevault-host/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'
```

响应中的 `access_token` 即为 Bearer Token。

## 本地开发测试

```bash
# 启动 NodeVault 后端
uvicorn backend.main:app --reload

# 验证 MCP SSE 端点可达
curl http://localhost:8000/mcp/sse
```
