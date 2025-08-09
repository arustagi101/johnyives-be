from __future__ import annotations

import json
import os
from pathlib import Path
import logging
from typing import Any, Dict
import shutil

from app.services.analysis import synthesize_suggestions
from app.models.agents import CopyPlan, StyleSystem

logger = logging.getLogger("ych.generator")


def generate_nextjs_project(
    audit_results: Dict[str, Any],
    preferences: Dict[str, Any],
    out_dir: str,
    copy_plan: CopyPlan | None = None,
    style: StyleSystem | None = None,
) -> Dict[str, Any]:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    logger.info("gen.start | out_dir=%s", out_dir)

    analysis = synthesize_suggestions(audit_results)
    tokens = analysis.get("plan", {}).get("design_tokens", {})
    brand_colors = preferences.get("brand_colors") or []
    if brand_colors:
        tokens["color_primary"] = brand_colors[0]
        logger.info("gen.tokens | color_primary=%s", tokens["color_primary"])
    if style is not None:
        tokens.update(style.design_tokens)

    project_dir = Path(out_dir) / "next_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    _write_package_json(project_dir)
    _write_next_config(project_dir)
    _write_tsconfig(project_dir)
    _write_tailwind_config(project_dir)
    _write_postcss_config(project_dir)
    _write_src(project_dir, tokens, analysis, copy_plan)

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


def _write_src(root: Path, tokens: Dict[str, Any], analysis: Dict[str, Any], copy_plan: CopyPlan | None) -> None:
    app_dir = root / "app"
    (app_dir).mkdir(parents=True, exist_ok=True)
    components_dir = root / "components"
    components_dir.mkdir(parents=True, exist_ok=True)
    styles_dir = root / "styles"
    styles_dir.mkdir(parents=True, exist_ok=True)

    (root / "next-env.d.ts").write_text(
        "/// <reference types=\"next\" />\n/// <reference types=\"next/image-types/global\" />\n"
    )

    # Build globals.css from design tokens (color, font)
    css_vars: Dict[str, Any] = {
        "--color-primary": tokens.get("color_primary", "#0ea5e9"),
        "--font-sans": tokens.get(
            "font_sans",
            "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji'",
        ),
    }
    root_vars = ";".join(f"{k}: {v}" for k, v in css_vars.items())
    globals_css = (
        f":root{{{root_vars};}}\n"
        "body{font-family: var(--font-sans);}\n"
        "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"
    )
    (styles_dir / "globals.css").write_text(globals_css)

    (app_dir / "layout.tsx").write_text(
        """import '../styles/globals.css';

export const metadata = { title: 'Generated Site' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang=\"en\"><body className=\"min-h-screen bg-white text-gray-900\">{children}</body></html>
  );
}
"""
    )

    # Apply improved copy to hero if available
    hero_title = "A Better UX"
    hero_subtitle = "Generated from your audit with sensible defaults."
    if copy_plan is not None:
        for blk in copy_plan.blocks:
            if blk.path == "/hero" and blk.improved_text:
                hero_title = blk.improved_text
            if blk.path == "/features" and blk.improved_text:
                hero_subtitle = blk.improved_text

    hero = f"""
export default function Hero() {{
  return (
    <section className=\"py-16 bg-[var(--color-primary)] text-white\">\n      <div className=\"mx-auto max-w-6xl px-6\">\n        <h1 className=\"text-4xl font-bold mb-4\">{hero_title}</h1>\n        <p className=\"text-lg\">{hero_subtitle}</p>\n      </div>\n    </section>\n  );\n}}\n"""
    (components_dir / "Hero.tsx").write_text(hero)

    # Feature cards with optional copy override from CopyPlan
    feature1 = "Fast, accessible, and responsive by default."
    feature2 = "Clear visual hierarchy with Tailwind."
    feature3 = "Easy to extend with components."
    if copy_plan is not None:
        for blk in copy_plan.blocks:
            if blk.path == "/features" and blk.improved_text:
                feature1 = blk.improved_text

    homepage = f"""import Hero from '../components/Hero';

export default function Page() {{
  return (
    <main>
      <Hero />
      <section className=\"mx-auto max-w-6xl px-6 py-12 grid gap-6 md:grid-cols-3\">\n        <div className=\"p-6 border rounded-lg\">{feature1}</div>\n        <div className=\"p-6 border rounded-lg\">{feature2}</div>\n        <div className=\"p-6 border rounded-lg\">{feature3}</div>
      </section>
    </main>
  );
}}
"""
    (app_dir / "page.tsx").write_text(homepage)

    # Include analysis JSON for reference
    (root / "analysis.json").write_text(json.dumps(analysis, indent=2))
