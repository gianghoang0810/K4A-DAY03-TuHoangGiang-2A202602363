"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return "[Mock Chatbot Response]: Tôi hỗ trợ giải thích kiểm định lỗi gán nhãn 2D/3D và quy trình Rework. Chế độ Chatbot không có công cụ tra cứu ca QC hoặc tạo phiếu Rework."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        # app.py nối từng kết quả Tool vào prompt theo định dạng này.
        sections = prompt.split("\n\nTool đã gọi: ")
        question = sections[0]
        question_lower = question.lower()

        def answer(content):
            return {"type": "text", "content": f"[Mock Agent Response]: {content}",
                    "thought": "Mock QC trả lời và kết thúc lượt xử lý."}

        def call(name, arguments):
            if name not in {tool.get("name") for tool in tools_schema}:
                return answer(f"Công cụ {name} chưa được cung cấp.")
            return {"type": "tool_call", "tool_name": name, "arguments": arguments,
                    "thought": f"Mock QC gọi {name} theo yêu cầu."}

        case_match = re.search(r"\bCASE-\d+\b", question, re.IGNORECASE)
        wants_rework = bool(re.search(r"tạo\s+(?:một\s+)?(?:phiếu\s+)?rework", question_lower))
        if "không tạo" in question_lower or "đừng tạo" in question_lower:
            wants_rework = False
        description_match = re.search(r"nội dung yêu cầu:\s*(.+)", question, re.IGNORECASE | re.DOTALL)
        requested_description = description_match.group(1).strip() if description_match else None

        if len(sections) > 1:
            latest = sections[-1]
            tool_name = latest.split("\n", 1)[0].strip()
            try:
                observation = json.JSONDecoder().raw_decode(latest.split("\nObservation: ", 1)[1])[0]
                if not isinstance(observation, dict):
                    raise ValueError("Observation phải là object")
            except (ValueError, IndexError):
                return answer("Không đọc được kết quả Tool; vui lòng kiểm tra dữ liệu trả về.")
            status = observation.get("status")
            if status == "NOT_FOUND":
                return answer("Không tìm thấy ca lỗi. Vui lòng kiểm tra lại mã QC Case.")
            if status != "SUCCESS":
                return answer(f"Tool không thành công: {json.dumps(observation, ensure_ascii=False)}")
            if tool_name == "create_rework_ticket":
                return answer(f"Kết quả tạo phiếu Rework: {json.dumps(observation, ensure_ascii=False)}")
            data = observation.get("data", {})
            if tool_name == "qc_case_query" and wants_rework:
                conditional = "nếu" in question_lower
                if conditional and ("qc_fail" not in question_lower or data.get("status") != "QC_FAIL"):
                    return answer(f"Chưa đủ điều kiện tạo Rework. Dữ liệu QC: {json.dumps(data, ensure_ascii=False)}")
                if not observation.get("case_id") or not data.get("error_type") or not data.get("description"):
                    return answer("Thiếu mã ca, loại lỗi hoặc mô tả lỗi để tạo Rework; vui lòng bổ sung.")
                return call("create_rework_ticket", {
                    "case_id": observation["case_id"],
                    "error_type": data["error_type"],
                    "description": requested_description or f"Khắc phục lỗi: {data['description']}"
                })
            return answer(f"Kết quả QC: {json.dumps(observation, ensure_ascii=False)}")

        if not case_match:
            if "tra cứu" in question_lower or wants_rework:
                if "hỗ trợ" not in question_lower:
                    return answer("Vui lòng cung cấp mã QC Case dạng CASE-1001.")
            return answer("Tôi hỗ trợ tra cứu lỗi gán nhãn 2D/3D bằng qc_case_query và tạo phiếu Rework bằng create_rework_ticket với mã ca, loại lỗi và mô tả cần sửa.")

        case_id = case_match.group().upper()
        error_match = re.search(r"\bloại lỗi\s+([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b", question, re.IGNORECASE)
        if wants_rework and "nếu" not in question_lower and error_match and requested_description:
            return call("create_rework_ticket", {
                "case_id": case_id, "error_type": error_match.group(1).upper(),
                "description": requested_description
            })
        return call("qc_case_query", {"case_id": case_id})


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
