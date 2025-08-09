from __future__ import annotations

import json
import os
from pathlib import Path
import logging
from typing import Any, Dict
import shutil

from app.services.analysis import synthesize_suggestions

logger = logging.getLogger("ych.generator")


def generate_nextjs_project(audit_results: Dict[str, Any], preferences: Dict[str, Any], out_dir: str) -> Dict[str, Any]:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    logger.info("gen.start | out_dir=%s", out_dir)

    analysis = synthesize_suggestions(audit_results)
    tokens = analysis.get("plan", {}).get("design_tokens", {})
    brand_colors = preferences.get("brand_colors") or []
    if brand_colors:
        tokens["color_primary"] = brand_colors[0]
        logger.info("gen.tokens | color_primary=%s", tokens["color_primary"])

    project_dir = Path(out_dir) / "next_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    _write_package_json(project_dir)
    _write_next_config(project_dir)
    _write_tsconfig(project_dir)
    _write_tailwind_config(project_dir)
    _write_postcss_config(project_dir)
    _write_src(project_dir, tokens, analysis)

    zip_path = shutil.make_archive(str(Path(out_dir) / "next_project"), "zip", project_dir)

    logger.info("gen.done | project_dir=%s", str(project_dir))
    return {
        "zip_path": zip_path,
        "project_dir": str(project_dir),
        "analysis": analysis,
    }


def _write_package_json(root: Path) -> None:
    pkg = {
        "name": "ych-generated",
        "private": True,
        "version": "0.1.0",
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
        },
        "dependencies": {
            "next": "^14.2.4",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "tailwindcss": "^3.4.7",
            "postcss": "^8.4.39",
            "autoprefixer": "^10.4.19"
        },
        "devDependencies": {
            "typescript": "^5.4.5"
        }
    }
    (root / "package.json").write_text(json.dumps(pkg, indent=2))


def _write_next_config(root: Path) -> None:
    content = """/** @type {import('next').NextConfig} */
const nextConfig = {};
module.exports = nextConfig;
"""
    (root / "next.config.js").write_text(content)


def _write_tsconfig(root: Path) -> None:
    content = {
        "compilerOptions": {
            "target": "ES2020",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True,
            "skipLibCheck": True,
            "strict": False,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "plugins": []
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
        "exclude": ["node_modules"]
    }
    (root / "tsconfig.json").write_text(json.dumps(content, indent=2))


def _write_tailwind_config(root: Path) -> None:
    content = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
"""
    (root / "tailwind.config.js").write_text(content)


def _write_postcss_config(root: Path) -> None:
    content = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""
    (root / "postcss.config.js").write_text(content)


def _write_src(root: Path, tokens: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    app_dir = root / "app"
    (app_dir).mkdir(parents=True, exist_ok=True)
    components_dir = root / "components"
    components_dir.mkdir(parents=True, exist_ok=True)
    styles_dir = root / "styles"
    styles_dir.mkdir(parents=True, exist_ok=True)

    (root / "next-env.d.ts").write_text("/// <reference types=\"next\" />\n/// <reference types=\"next/image-types/global\" />\n")

    (styles_dir / "globals.css").write_text(
        ":root{--color-primary: %s;}\n@tailwind base;\n@tailwind components;\n@tailwind utilities;\n" % (tokens.get("color_primary", "#0ea5e9"))
    )

    (app_dir / "layout.tsx").write_text(
        """export const metadata = { title: 'Generated Site' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang=\"en\"><body className=\"min-h-screen bg-white text-gray-900\">{children}</body></html>
  );
}
"""
    )

    hero = f"""
export default function Hero() {{
  return (
    <section className=\"py-16 bg-[var(--color-primary)] text-white\">
      <div className=\"mx-auto max-w-6xl px-6\">
        <h1 className=\"text-4xl font-bold mb-4\">A Better UX</h1>
        <p className=\"text-lg\">Generated from your audit with sensible defaults.</p>
      </div>
    </section>
  );
}}
"""
    (components_dir / "Hero.tsx").write_text(hero)

    homepage = """import './globals.css';
import Hero from '../components/Hero';

export default function Page() {
  return (
    <main>
      <Hero />
      <section className=\"mx-auto max-w-6xl px-6 py-12 grid gap-6 md:grid-cols-3\">
        <div className=\"p-6 border rounded-lg\">Fast, accessible, and responsive by default.</div>
        <div className=\"p-6 border rounded-lg\">Clear visual hierarchy with Tailwind.</div>
        <div className=\"p-6 border rounded-lg\">Easy to extend with components.</div>
      </section>
    </main>
  );
}
"""
    (app_dir / "page.tsx").write_text(homepage)

    # Include analysis JSON for reference
    (root / "analysis.json").write_text(json.dumps(analysis, indent=2))
