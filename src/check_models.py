"""List Gemini models or test native tool calling without executing a tool."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", nargs="+", metavar="MODEL")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    key = os.getenv("GEMINI_API_KEY")
    if not key or key == "your_gemini_api_key_here":
        parser.error("Configure GEMINI_API_KEY in .env first.")

    failed = False
    with genai.Client(api_key=key, http_options={"timeout": 20000}) as client:
        if not args.test:
            for model in client.models.list():
                if "generateContent" in (model.supported_actions or []):
                    print(model.name.removeprefix("models/"))
            print("Listed models may still require access or quota. Use --test MODEL to verify.")
            return

        for model in args.test:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents="Call qc_case_query with case_id CASE-1001.",
                    config=types.GenerateContentConfig(
                        tools=[{"function_declarations": [{
                            "name": "qc_case_query",
                            "description": "Look up a QC case.",
                            "parameters": {
                                "type": "object",
                                "properties": {"case_id": {"type": "string"}},
                                "required": ["case_id"]
                            }
                        }]}],
                        tool_config={"function_calling_config": {"mode": "ANY"}},
                        temperature=0.2
                    )
                )
                calls = response.function_calls or []
                if any(c.name == "qc_case_query" and dict(c.args or {}).get("case_id") == "CASE-1001" for c in calls):
                    print(f"PASS {model}: native tool calling works (tool not executed).")
                else:
                    failed = True
                    print(f"FAIL {model}: no matching tool call returned.")
            except Exception as exc:
                failed = True
                print(f"FAIL {model}: {str(exc).replace(key, '[REDACTED]')}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
