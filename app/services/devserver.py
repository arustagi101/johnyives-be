from __future__ import annotations

import logging
from typing import Any, Dict, Optional


logger = logging.getLogger("ych.devserver")


DEFAULT_TEMPLATE_REPO = "https://github.com/freestyle-sh/freestyle-base-nextjs-shadcn"


def provision_dev_server(api_key: str, template_repo_url: Optional[str] = None) -> Dict[str, Any]:
    """Create a Freestyle Git repository from a Next.js template and request a Dev Server.

    Returns a dict with keys: repo_id, ephemeral_url, mcp_ephemeral_url, code_server_url,
    and raw handles: commit_and_push, fs, process, shutdown.
    """
    try:
        import freestyle  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("freestyle SDK not installed. Add 'freestyle' to requirements.") from exc

    client = freestyle.Freestyle(api_key)

    repo = client.create_repository(
        name="ych-nextjs-project",
        public=True,
        source=freestyle.CreateRepoSource.from_dict(
            {
                "type": "git",
                "url": template_repo_url or DEFAULT_TEMPLATE_REPO,
            }
        ),
    )
    logger.info("devserver.repo.created | repo_id=%s", repo.repo_id)

    dev_server = client.request_dev_server(repo_id=repo.repo_id)
    logger.info("devserver.requested | url=%s", dev_server.ephemeral_url)

    return {
        "repo_id": repo.repo_id,
        "ephemeral_url": dev_server.ephemeral_url,
        "mcp_ephemeral_url": dev_server.mcp_ephemeral_url,
        "code_server_url": dev_server.code_server_url,
        "commit_and_push": dev_server.commit_and_push,
        "fs": dev_server.fs,
        "process": dev_server.process,
        "shutdown": dev_server.shutdown,
        "_dev_server": dev_server,  # raw handle if needed
    }


def connect_dev_server(api_key: str, repo_id: str) -> Dict[str, Any]:
    """Connect to an existing Freestyle repo's Dev Server (assumes repo already exists).

    Returns the same handle structure as provision_dev_server.
    """
    try:
        import freestyle  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("freestyle SDK not installed. Add 'freestyle' to requirements.") from exc

    client = freestyle.Freestyle(api_key)
    dev_server = client.request_dev_server(repo_id=repo_id)
    logger.info("devserver.connected | repo_id=%s url=%s", repo_id, dev_server.ephemeral_url)
    return {
        "repo_id": repo_id,
        "ephemeral_url": dev_server.ephemeral_url,
        "mcp_ephemeral_url": dev_server.mcp_ephemeral_url,
        "code_server_url": dev_server.code_server_url,
        "commit_and_push": dev_server.commit_and_push,
        "fs": dev_server.fs,
        "process": dev_server.process,
        "shutdown": dev_server.shutdown,
        "_dev_server": dev_server,
    }


def write_next_homepage(fs: Any, page_tsx: str) -> None:
    """Write the Next.js homepage into the template repo using Dev Server FS."""
    fs.write_file("app/page.tsx", page_tsx)


def verify_next_build(process: Any) -> Dict[str, str]:
    """Run npm install and npm run build to ensure code compiles."""
    try:
        result_install = process.exec("npm ci || npm install")
        logger.info("devserver.npm_install | ok")
    except Exception as exc:  # pragma: no cover
        logger.warning("devserver.npm_install.failed | %s", exc)
        result_install = {"stdout": "", "stderr": str(exc)}

    result_build = process.exec("npm run build")
    logger.info("devserver.npm_build | ok")
    return {"install": str(result_install), "build": str(result_build)}


