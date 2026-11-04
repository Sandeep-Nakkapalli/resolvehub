import os
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
STATIC_ROOT = ROOT / "staticfiles"
OUTPUT = ROOT / "dist"
API_URL = os.getenv("DJANGO_API_URL", "https://resolvehub-api.onrender.com").rstrip("/")


def main():
    if not API_URL.startswith("https://"):
        raise SystemExit("DJANGO_API_URL must be an HTTPS origin for the Render API.")
    if not STATIC_ROOT.is_dir():
        raise SystemExit("Run collectstatic before building the Netlify frontend.")

    if OUTPUT.exists():
        if OUTPUT.resolve() != (ROOT / "dist").resolve():
            raise SystemExit("Refusing to clean an unexpected Netlify output directory.")
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    for page in FRONTEND.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        html = re.sub(r"\{%\s*load\s+static\s*%\}", "", html)
        html = re.sub(
            r"\{%\s*static\s+['\"]([^'\"]+)['\"]\s*%\}",
            lambda match: f"/static/{match.group(1)}",
            html,
        )
        if "{%" in html or "{{" in html:
            raise SystemExit(f"Unconverted Django template tag in {page.name}.")
        (OUTPUT / page.name).write_text(html, encoding="utf-8")

    for asset in STATIC_ROOT.rglob("*"):
        if not asset.is_file() or asset.suffix.lower() == ".html":
            continue
        destination = OUTPUT / "static" / asset.relative_to(STATIC_ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, destination)
    redirects = (
        f"/api/* {API_URL}/api/:splat 200\n"
        f"/django-admin/* {API_URL}/django-admin/:splat 200\n"
    )
    (OUTPUT / "_redirects").write_text(redirects, encoding="utf-8")
    print(f"Prepared {len(list(FRONTEND.glob('*.html')))} pages for Netlify.")
    print(f"Proxied API routes to {API_URL}.")


if __name__ == "__main__":
    main()
