"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer
phục vụ cho MCP Server của QC Assistant.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS
# ==============================================================================

TOOLS_SCHEMA = [
    {
        "name": "qc_case_query",
        "description": "Tra cứu thông tin ca lỗi gán nhãn 2D/3D bằng mã QC Case.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {
                    "type": "string",
                    "description": "Mã QC Case cần tra cứu, ví dụ: 'CASE-1001'"
                }
            },
            "required": ["case_id"]
        }
    },

    {
        "name": "create_rework_ticket",
        "description": "Tạo phiếu Rework cho ca gán nhãn 2D/3D bị lỗi.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_id": {
                    "type": "string",
                    "description": "Mã QC Case cần tạo Rework"
                },
                "error_type": {
                    "type": "string",
                    "description": "Loại lỗi, ví dụ: 'BBOX_MISALIGNED'"
                },
                "description": {
                    "type": "string",
                    "description": "Mô tả lỗi cần sửa"
                }
            },
            "required": ["case_id", "error_type", "description"]
        }
    }
]

# ==============================================================================
# 2. MOCK DATABASE & EXECUTION LAYER
# ==============================================================================

MOCK_DATABASE = {
    "CASE-1001": {
        "annotation_type": "3D",
        "object_class": "Car",
        "error_type": "CUBOID_MISALIGNED",
        "description": "3D Cuboid lệch so với Point Cloud.",
        "annotator": "ANN-001",
        "status": "QC_FAIL"
    },
    "CASE-1002": {
        "annotation_type": "2D",
        "object_class": "Pedestrian",
        "error_type": "BBOX_MISALIGNED",
        "description": "Bounding Box chưa bao phủ đầy đủ đối tượng.",
        "annotator": "ANN-002",
        "status": "QC_FAIL"
    }
}


def execute_qc_case_query(case_id: str) -> str:
    """Thực thi tra cứu QC Case"""
    case = MOCK_DATABASE.get(case_id.strip().upper())

    if case:
        return json.dumps({
            "status": "SUCCESS",
            "case_id": case_id,
            "data": case
        }, ensure_ascii=False)

    return json.dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy QC Case '{case_id}'"
    }, ensure_ascii=False)


def execute_create_rework_ticket(
    case_id: str,
    error_type: str,
    description: str
) -> str:
    """Thực thi tạo phiếu Rework"""
    return json.dumps({
        "status": "SUCCESS",
        "rework_id": f"RW-{case_id}-01",
        "case_id": case_id,
        "error_type": error_type,
        "description": description,
        "message": f"Đã tạo phiếu Rework cho {case_id}."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "qc_case_query": execute_qc_case_query,
    "create_rework_ticket": execute_create_rework_ticket
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({
                "status": "EXECUTION_ERROR",
                "error": str(e)
            }, ensure_ascii=False)

    return json.dumps({
        "status": "UNKNOWN_TOOL",
        "error": f"Tool '{tool_name}' không tồn tại!"
    }, ensure_ascii=False)


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if {tool["name"] for tool in TOOLS_SCHEMA} != set(TOOL_ROUTER):
        raise RuntimeError("Tên tool trong TOOLS_SCHEMA và TOOL_ROUTER không khớp.")

    print(
        f"[TOOLS CHECK]: Đã đăng ký thành công {len(TOOLS_SCHEMA)} "
        "Native Tools trong TOOLS_SCHEMA!"
    )

    test_calls = [
        ("qc_case_query", {"case_id": "CASE-1001"}),
        ("create_rework_ticket", {
            "case_id": "CASE-1001",
            "error_type": "CUBOID_MISALIGNED",
            "description": "3D Cuboid lệch so với Point Cloud."
        })
    ]
    for tool_name, arguments in test_calls:
        result = json.loads(dispatch_tool_call(tool_name, arguments))
        if result.get("status") != "SUCCESS":
            raise RuntimeError(f"Gọi thử {tool_name} thất bại: {result}")
        print(f"Kết quả gọi thử {tool_name}: Status {result['status']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
