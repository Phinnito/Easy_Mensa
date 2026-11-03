import json
from pathlib import Path

from src.models.recipe import Recipe


ROOT = Path(__file__).resolve().parents[2]
RECIPES_DIR = ROOT / "data" / "recipes"
IMAGES_DIR = ROOT / "images" / "recipes"


def ensure_directories() -> None:
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def recipe_path(recipe_id: str) -> Path:
    return RECIPES_DIR / f"{recipe_id}.json"


def save_recipe(recipe: Recipe) -> Path:
    ensure_directories()
    path = recipe_path(recipe.id)
    path.write_text(
        json.dumps(
            recipe.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def load_recipe(path: Path) -> Recipe:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Recipe.model_validate(raw)


def list_recipes() -> list[Recipe]:
    ensure_directories()
    recipes: list[Recipe] = []

    for path in sorted(RECIPES_DIR.glob("*.json")):
        try:
            recipes.append(load_recipe(path))
        except (OSError, json.JSONDecodeError, ValueError):
            continue

    return recipes


def save_recipe_image(recipe_id: str, uploaded_file) -> str | None:
    if uploaded_file is None:
        return None

    ensure_directories()

    original_name = Path(uploaded_file.name)
    suffix = original_name.suffix.lower() or ".jpg"
    filename = f"{recipe_id}{suffix}"
    path = IMAGES_DIR / filename
    path.write_bytes(uploaded_file.getvalue())

    return f"images/recipes/{filename}"
