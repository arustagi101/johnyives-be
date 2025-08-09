#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
import shutil
import webbrowser


RUNTIME_BASE = Path(__file__).resolve().parents[1] / "runtime" / "generate"


def choose_package_manager() -> str:
    for tool in ("pnpm", "yarn", "npm"):
        if shutil.which(tool):
            return tool
    raise RuntimeError("No package manager found. Install pnpm, yarn, or npm.")


def find_latest_project_dir() -> Optional[Path]:
    if not RUNTIME_BASE.exists():
        return None
    job_dirs = [p for p in RUNTIME_BASE.iterdir() if p.is_dir()]
    if not job_dirs:
        return None
    job_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for job_dir in job_dirs:
        proj = job_dir / "next_project"
        if (proj / "package.json").exists():
            return proj
    return None


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> int:
    process = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env or os.environ.copy(),
    )
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return 130


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a generated Next.js site")
    parser.add_argument("--project-dir", type=str, help="Path to generated next_project directory")
    parser.add_argument("--prod", action="store_true", help="Build and start (production mode)")
    parser.add_argument("--port", type=int, default=3000, help="Port to run the server on")
    parser.add_argument("--install", action="store_true", help="Force install dependencies")
    parser.add_argument("--open", action="store_true", help="Open the site in the default browser")
    args = parser.parse_args()

    if args.project_dir:
        project_dir = Path(args.project_dir).resolve()
    else:
        project_dir = find_latest_project_dir() or Path()

    if not project_dir or not (project_dir / "package.json").exists():
        print("Could not locate a generated Next.js project. Provide --project-dir or generate one first.")
        print(f"Looked under: {RUNTIME_BASE}")
        return 1

    print(f"Using project: {project_dir}")

    pm = choose_package_manager()
    print(f"Using package manager: {pm}")

    # Install deps if requested or node_modules missing
    if args.install or not (project_dir / "node_modules").exists():
        print("Installing dependencies...")
        code = run([pm, "install"], cwd=project_dir)
        if code != 0:
            return code

    env = os.environ.copy()
    env["PORT"] = str(args.port)

    if args.open:
        webbrowser.open_new_tab(f"http://localhost:{args.port}")

    if args.prod:
        print("Building...")
        code = run([pm, "run", "build"], cwd=project_dir, env=env)
        if code != 0:
            return code
        print(f"Starting on http://localhost:{args.port} ... (Ctrl+C to stop)")
        return run([pm, "run", "start"], cwd=project_dir, env=env)
    else:
        print(f"Starting dev server on http://localhost:{args.port} ... (Ctrl+C to stop)")
        return run([pm, "run", "dev"], cwd=project_dir, env=env)


if __name__ == "__main__":
    sys.exit(main())


