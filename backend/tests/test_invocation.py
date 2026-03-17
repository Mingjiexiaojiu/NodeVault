"""Unit tests for invoke_node_by_name (2.4)"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.invocation import (
    NodeNotFoundError,
    NodeVersionNotFoundError,
    invoke_node_by_name,
)


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def sample_node():
    node = MagicMock()
    node.id = uuid.uuid4()
    node.name = "detect_fund_pool"
    node.status = "active"
    node.invocation_count = 0
    return node


@pytest.fixture
def sample_version(sample_node):
    version = MagicMock()
    version.version = "1.0.0"
    version.node_id = sample_node.id
    version.is_default = True
    version.runtime_config = {"type": "http", "endpoint": "http://example.com/invoke"}
    return version


@pytest.mark.asyncio
async def test_invoke_node_by_name_not_found(mock_db, mock_user):
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    with pytest.raises(NodeNotFoundError, match="No active node named"):
        await invoke_node_by_name("nonexistent", {}, mock_user, mock_db)


@pytest.mark.asyncio
async def test_invoke_node_no_default_version(mock_db, mock_user, sample_node):
    first_call = MagicMock()
    first_call.scalar_one_or_none.return_value = sample_node
    second_call = MagicMock()
    second_call.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(side_effect=[first_call, second_call])

    with pytest.raises(NodeVersionNotFoundError, match="no default version"):
        await invoke_node_by_name("detect_fund_pool", {}, mock_user, mock_db)


@pytest.mark.asyncio
async def test_invoke_node_by_name_success(mock_db, mock_user, sample_node, sample_version):
    first_call = MagicMock()
    first_call.scalar_one_or_none.return_value = sample_node
    second_call = MagicMock()
    second_call.scalar_one_or_none.return_value = sample_version
    mock_db.execute = AsyncMock(side_effect=[first_call, second_call, MagicMock()])
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()

    with patch("backend.core.invocation.RuntimeDispatcher") as mock_dispatcher:
        mock_executor = AsyncMock()
        mock_executor.execute = AsyncMock(return_value=({"result": "ok"}, 42))
        mock_dispatcher.get_executor.return_value = mock_executor

        result = await invoke_node_by_name("detect_fund_pool", {"data": []}, mock_user, mock_db)

    assert result["output"] == {"result": "ok"}
    assert result["latency_ms"] == 42
    assert result["version"] == "1.0.0"
    assert result["node_name"] == "detect_fund_pool"
