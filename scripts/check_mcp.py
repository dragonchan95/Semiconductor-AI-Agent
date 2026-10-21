import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent


async def main():
    args = StdioServerParameters(command=sys.executable, args=[str(ROOT / "mcp_server.py")],
        env={**os.environ, "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false"})
    async with stdio_client(args) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            assert names == ["list_datasets", "propose_experiment", "get_experiment_result", "explain_model_candidates"]
            assert not any("approv" in name or "execute" in name for name in names)
            result = await session.call_tool("list_datasets", {})
            assert not getattr(result, "is_error", getattr(result, "isError", False))
            resources = await session.read_resource("semiconductor://knowledge/leakage")
            candidates = await session.call_tool('explain_model_candidates', {'modality':'tabular'})
            assert not getattr(candidates, 'isError', False)
            assert "Validation" in resources.contents[0].text
            receipt = {"transport": "stdio", "handshake": True, "tools": names,
                       "approval_or_execution_tool_exposed": False,
                       "dataset_tool_ok": True, "knowledge_resource_ok": True, 'model_explanation_tool_ok': True}
    (ROOT / "docs/evaluation/mcp_check.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
    print(receipt)


if __name__ == "__main__":
    asyncio.run(main())
