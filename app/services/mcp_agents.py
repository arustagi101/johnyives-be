from __future__ import annotations

import json
import logging
from typing import Any, Dict

import dspy  # type: ignore

from app.models.agents import CopyPlan


logger = logging.getLogger("ych.mcp.react")


# Note: We rely on the ReAct agent end-to-end; no local fallbacks or hardcoded TSX are used.


class NextPageTaskSig(dspy.Signature):  # type: ignore
    """Update or create app/page.tsx using available tools.

    Inputs:
    - target_path: file path to update (e.g., app/page.tsx)
    - style_guide: textual criteria
    - copy_plan_json: JSON of CopyPlan
    

    Outputs:
    - status: brief status string
    """

    target_path: str = dspy.InputField()
    style_guide: str = dspy.InputField()
    copy_plan_json: str = dspy.InputField()
    status: str = dspy.OutputField()


def react_generate_and_build(ds: Dict[str, Any], copy_plan: CopyPlan, style_guide: str) -> Dict[str, Any]:
    """Run a DSPy ReAct agent using Freestyle dev server tools to edit code and verify build.

    Tools mirror the Freestyle MCP toolset (readFile, writeFile, exec, npmInstall, commitAndPush)
    as Python callables, per DSPy ReAct docs (`https://dspy.ai/api/modules/ReAct/?h=react`).
    """

    def tool_read_file(path: str) -> str:
        logger.info("mcp.readFile | path=%s", path)
        content = ds["fs"].read_file(path)
        logger.info("mcp.readFile.done | bytes=%s", len(content or ""))
        return content

    def tool_write_file(path: str, content: str) -> str:
        logger.info("mcp.writeFile | path=%s | size=%s", path, len(content or ""))
        ds["fs"].write_file(path, content)
        logger.info("mcp.writeFile.done | path=%s", path)
        return "ok"

    def tool_exec(command: str) -> str:
        logger.info("mcp.exec | cmd=%s", command)
        res = ds["process"].exec(command)
        logger.info("mcp.exec.done | cmd=%s", command)
        return str(res)

    def tool_npm_install() -> str:
        logger.info("mcp.npmInstall | start")
        ds["process"].exec("npm ci || npm install")
        logger.info("mcp.npmInstall.done")
        return "ok"

    def tool_npm_lint() -> str:
        logger.info("mcp.npmLint | start")
        res = ds["process"].exec("npm run lint")
        logger.info("mcp.npmLint.done")
        return str(res)

    def tool_commit_and_push(message: str) -> str:
        logger.info("mcp.commitAndPush | msg=%s", message)
        ds["commit_and_push"](message)
        logger.info("mcp.commitAndPush.done")
        return "ok"

    tools = [
        dspy.Tool(tool_read_file),
        dspy.Tool(tool_write_file),
        dspy.Tool(tool_exec),
        dspy.Tool(tool_npm_install),
        dspy.Tool(tool_npm_lint),
        dspy.Tool(tool_commit_and_push),
    ]

    react = dspy.ReAct(signature=NextPageTaskSig, tools=tools, max_iters=12)
    logger.info("react.start | target=app/page.tsx")
    prediction = react(
        target_path="app/page.tsx",
        style_guide=style_guide,
        copy_plan_json=json.dumps(copy_plan.model_dump()),
    )
    logger.info("react.done | status=%s", getattr(prediction, "status", ""))

    # Ensure lint and build before pushing
    lint_ok = True
    build_ok = True
    try:
        tool_npm_install()
        tool_npm_lint()
    except Exception as exc:
        lint_ok = False
        logger.exception("mcp.lint.failed: %s", exc)
    try:
        logger.info("mcp.build | npm run build")
        ds["process"].exec("npm run build")
        logger.info("mcp.build.done")
    except Exception as exc:
        build_ok = False
        logger.exception("mcp.build.failed: %s", exc)

    if lint_ok and build_ok:
        try:
            tool_commit_and_push("Apply copy updates via DSPy ReAct")
        except Exception as exc:
            logger.exception("mcp.commit.failed: %s", exc)

    return {
        "status": getattr(prediction, "status", "done"),
        "lint": "ok" if lint_ok else "failed",
        "build": "ok" if build_ok else "failed",
    }


