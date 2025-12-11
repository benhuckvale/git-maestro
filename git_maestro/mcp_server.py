"""MCP (Model Context Protocol) server for git-maestro."""

import json
import sys
from pathlib import Path
from typing import Any
import inspect

from git_maestro.state import RepoState
from git_maestro.actions import DownloadJobTracesAction


class MCPServer:
    """MCP server implementing git-maestro tools."""

    def __init__(self):
        self.version = "2024-11-05"
        self.dev_installation_error: str | None = None
        self._check_dev_installation_safety()
        self.tools = {
            "download_job_traces": {
                "description": "Download GitHub Actions job traces/logs for failed jobs in the current repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Path to the git repository (defaults to current directory)",
                        }
                    },
                    "required": [],
                },
            }
        }

    def _check_dev_installation_safety(self) -> None:
        """
        Refuse to start if Claude is actively modifying a development installation.
        This prevents privilege escalation where MCP (running outside sandbox)
        could be modified by Claude while it's being used.
        """
        try:
            # Get the path to the git_maestro module
            module_file = inspect.getfile(sys.modules["git_maestro"])
            module_path = Path(module_file).parent.parent.resolve()

            # Check if this looks like a development installation (has .git, pyproject.toml, etc.)
            is_dev = (
                (module_path / ".git").exists()
                or (module_path / "pyproject.toml").exists()
            )

            if is_dev:
                # Only refuse if Claude is actively working in this directory
                claude_cwd = Path.cwd().resolve()
                if claude_cwd == module_path or module_path in claude_cwd.parents:
                    # Claude is working inside the git-maestro dev directory
                    self.dev_installation_error = (
                        f"git-maestro MCP refuses to start from a development installation "
                        f"at {module_path} while Claude is working in {claude_cwd}. MCP runs outside "
                        f"any AI assistant sandbox, so Claude modifying the same code that MCP is "
                        f"running creates a security risk. Please run Claude from a different directory."
                    )
        except Exception:
            # Silently ignore any errors in this safety check
            pass

    def handle_message(self) -> None:
        """Handle incoming MCP messages from stdin."""
        # If there's a dev installation error, reject all messages
        if self.dev_installation_error:
            for line in sys.stdin:
                try:
                    message = json.loads(line)
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": self.dev_installation_error,
                        },
                        "id": message.get("id"),
                    }
                    print(json.dumps(error_response), flush=True)
                except json.JSONDecodeError:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                        },
                        "id": None,
                    }
                    print(json.dumps(error_response), flush=True)
                except Exception as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}",
                        },
                        "id": None,
                    }
                    print(json.dumps(error_response), flush=True)
        else:
            for line in sys.stdin:
                try:
                    message = json.loads(line)
                    response = self.process_message(message)
                    print(json.dumps(response), flush=True)
                except json.JSONDecodeError:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                        },
                        "id": None,
                    }
                    print(json.dumps(error_response), flush=True)
                except Exception as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}",
                        },
                        "id": None,
                    }
                    print(json.dumps(error_response), flush=True)

    def process_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Process an MCP message."""
        jsonrpc = message.get("jsonrpc", "2.0")
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        if method == "initialize":
            return self.handle_initialize(msg_id)
        elif method == "tools/list":
            return self.handle_list_tools(msg_id)
        elif method == "tools/call":
            return self.handle_call_tool(params, msg_id)
        else:
            return {
                "jsonrpc": jsonrpc,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
                "id": msg_id,
            }

    def handle_initialize(self, msg_id: Any) -> dict[str, Any]:
        """Handle initialize request."""
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": self.version,
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "git-maestro",
                    "version": "0.1.0",
                },
            },
            "id": msg_id,
        }

    def handle_list_tools(self, msg_id: Any) -> dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            {
                "name": name,
                "description": info["description"],
                "inputSchema": info["inputSchema"],
            }
            for name, info in self.tools.items()
        ]
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": tools,
            },
            "id": msg_id,
        }

    def handle_call_tool(
        self, params: dict[str, Any], msg_id: Any
    ) -> dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        tool_input = params.get("arguments", {})

        if tool_name == "download_job_traces":
            return self.call_download_job_traces(tool_input, msg_id)
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}",
                },
                "id": msg_id,
            }

    def call_download_job_traces(
        self, tool_input: dict[str, Any], msg_id: Any
    ) -> dict[str, Any]:
        """Call the download_job_traces tool."""
        try:
            repo_path = tool_input.get("repo_path", ".")
            path = Path(repo_path).resolve()

            # Get the current state
            state = RepoState(path)

            # Create and execute the action
            action = DownloadJobTracesAction()

            if not action.is_applicable(state):
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "No failed jobs found or GitHub Actions haven't been checked yet.",
                            }
                        ],
                    },
                    "id": msg_id,
                }

            success = action.execute(state)

            if success:
                traces_path = state.get_fact("github_actions_traces_path", "")
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Successfully downloaded job traces to: {traces_path}",
                            }
                        ],
                    },
                    "id": msg_id,
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "Failed to download job traces. Check logs for details.",
                            }
                        ],
                    },
                    "id": msg_id,
                }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Error executing tool: {str(e)}",
                },
                "id": msg_id,
            }


def main():
    """Main entry point for the MCP server."""
    server = MCPServer()
    server.handle_message()


if __name__ == "__main__":
    main()
