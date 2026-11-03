from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SITE = ROOT / "site"
OUTPUT = ROOT / "_site"
RECIPES_DIR = ROOT / "data" / "recipes"
IMAGES_DIR = ROOT / "images" / "recipes"


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    shutil.copytree(SOURCE_SITE, OUTPUT)

    recipes = []
    for path in sorted(RECIPES_DIR.glob("*.json")):
        try:
            recipes.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue

    (OUTPUT / "recipes.json").write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    target_images = OUTPUT / "images" / "recipes"
    target_images.mkdir(parents=True, exist_ok=True)

    if IMAGES_DIR.exists():
        for image in IMAGES_DIR.iterdir():
            if image.is_file() and not image.name.startswith("."):
                shutil.copy2(image, target_images / image.name)

    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Exported {len(recipes)} recipes to {OUTPUT}")


if __name__ == "__main__":
    main()
