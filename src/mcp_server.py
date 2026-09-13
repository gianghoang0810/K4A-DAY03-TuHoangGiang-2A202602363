"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server cung cấp công cụ cho QC Assistant.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class MCPQCServer:
    """
    Giả lập MCP Server cho Trợ lý Kiểm định Chất lượng (QC Assistant)
    """

    def __init__(self, server_name: str = "qc-assistant-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA

    def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        [TASK 2.1] Thực thi Tool thông qua MCP Server.
        """

        # 1. Gọi Tool Router
        result_json = dispatch_tool_call(tool_name, arguments)

        # 2. Chuyển chuỗi JSON thành Python Dictionary
        content = json.loads(result_json)

        # 3. Đóng gói phản hồi theo JSON-RPC 2.0
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


if __name__ == "__main__":

    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (qc-assistant-mcp-server)")
    print("==========================================================")

    server = MCPQCServer()

    tools = server.list_tools()

    print(
        f"✅ Khởi tạo thành công MCP Server: "
        f"{server.server_name} (Version: {server.version})"
    )

    print(f"📦 Số lượng Tools công bố: {len(tools)}")

    # Kiểm tra Tool Schema
    rework_tool = next(
        (t for t in tools if t.get("name") == "create_rework_ticket"),
        None
    )

    if rework_tool and not rework_tool.get(
        "parameters", {}
    ).get("properties"):

        print(
            "⏳ Tool 'create_rework_ticket' "
            "chưa được định nghĩa schema đầy đủ."
        )

    else:

        print(
            "✅ Tool 'create_rework_ticket' "
            "đã có schema đầy đủ."
        )

    # Kiểm tra TASK 2.1
    test_result = server.call_tool(
        "qc_case_query",
        {
            "case_id": "CASE-1001"
        }
    )

    if not test_result:

        print(
            "⏳ [TODO 2.1]: Hàm call_tool() đang trả về rỗng."
        )

    else:

        print(
            "✅ [TODO 2.1]: Test dispatch tool "
            "'qc_case_query' thành công:"
        )

        print(
            f"   Phản hồi JSON-RPC: "
            f"{json.dumps(test_result, ensure_ascii=False)}"
        )