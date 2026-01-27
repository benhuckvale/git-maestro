"""Tests for MCP stdio transport compliance."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _frame(message: dict) -> bytes:
    body = json.dumps(message).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    return header + body


def _parse_framed_messages(raw: bytes) -> list[dict]:
    messages: list[dict] = []
    offset = 0

    while offset < len(raw):
        header_end = raw.find(b"\r\n\r\n", offset)
        assert header_end != -1

        header_text = raw[offset:header_end].decode("utf-8", errors="replace")
        headers: dict[str, str] = {}
        for line in header_text.split("\r\n"):
            if not line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        content_length = int(headers["content-length"])
        body_start = header_end + 4
        body_end = body_start + content_length
        body = raw[body_start:body_end]
        assert len(body) == content_length

        decoded = json.loads(body.decode("utf-8"))
        assert isinstance(decoded, dict)
        messages.append(decoded)

        offset = body_end

    return messages


def _json_lines(*messages: dict) -> bytes:
    return b"".join(json.dumps(m).encode("utf-8") + b"\n" for m in messages)


def _parse_json_lines(raw: bytes) -> list[dict]:
    parsed: list[dict] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        decoded = json.loads(stripped.decode("utf-8"))
        assert isinstance(decoded, dict)
        parsed.append(decoded)
    return parsed


def _run_mcp_server_stdin_stdout(
    input_bytes: bytes, cwd: Path
) -> subprocess.CompletedProcess:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )

    return subprocess.run(
        [sys.executable, "-c", "from git_maestro.cli import main_mcp; main_mcp()"],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(cwd),
        env=env,
        timeout=10,
    )


def test_mcp_framed_initialize_then_tools_list(temp_dir: Path):
    input_bytes = _frame(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    ) + _frame({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})

    proc = _run_mcp_server_stdin_stdout(input_bytes, cwd=temp_dir)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")

    responses = _parse_framed_messages(proc.stdout)
    assert [r.get("id") for r in responses] == [1, 2]
    assert "protocolVersion" in responses[0]["result"]
    assert isinstance(responses[1]["result"].get("tools"), list)


@pytest.mark.parametrize("method", ["initialized", "notifications/initialized"])
def test_mcp_does_not_respond_to_initialized_notification(temp_dir: Path, method: str):
    input_bytes = (
        _frame({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        + _frame({"jsonrpc": "2.0", "method": method, "params": {}})
        + _frame({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    )

    proc = _run_mcp_server_stdin_stdout(input_bytes, cwd=temp_dir)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")

    responses = _parse_framed_messages(proc.stdout)
    assert [r.get("id") for r in responses] == [1, 2]


def test_mcp_json_lines_initialize_then_tools_list(temp_dir: Path):
    input_bytes = _json_lines(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )

    proc = _run_mcp_server_stdin_stdout(input_bytes, cwd=temp_dir)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")

    responses = _parse_json_lines(proc.stdout)
    assert [r.get("id") for r in responses] == [1, 2]
    assert "protocolVersion" in responses[0]["result"]
    assert isinstance(responses[1]["result"].get("tools"), list)


@pytest.mark.parametrize("method", ["initialized", "notifications/initialized"])
def test_mcp_json_lines_does_not_respond_to_initialized_notification(
    temp_dir: Path, method: str
):
    input_bytes = _json_lines(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": method, "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )

    proc = _run_mcp_server_stdin_stdout(input_bytes, cwd=temp_dir)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")

    responses = _parse_json_lines(proc.stdout)
    assert [r.get("id") for r in responses] == [1, 2]
