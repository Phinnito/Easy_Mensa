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


def get_recipe(recipe_id: str) -> Recipe | None:
    path = recipe_path(recipe_id)
    if not path.exists():
        return None
    try:
        return load_recipe(path)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def list_recipes() -> list[Recipe]:
    ensure_directories()
    recipes: list[Recipe] = []

    for path in sorted(RECIPES_DIR.glob("*.json")):
        try:
            recipes.append(load_recipe(path))
        except (OSError, json.JSONDecodeError, ValueError):
            continue

    return recipes


def delete_recipe(recipe_id: str) -> bool:
    """Delete one recipe JSON and its referenced image, if present."""
    ensure_directories()
    recipe = get_recipe(recipe_id)
    path = recipe_path(recipe_id)

    if not path.exists():
        return False

    if recipe and recipe.image:
        image_path = ROOT / recipe.image
        try:
            image_path.resolve().relative_to(IMAGES_DIR.resolve())
        except ValueError:
            image_path = None

        if image_path and image_path.exists():
            image_path.unlink()

    path.unlink()
    return True


def save_recipe_image(
    recipe_id: str,
    uploaded_file,
    existing_image: str | None = None,
) -> str | None:
    """Save a replacement image, or preserve the existing image when no upload."""
    if uploaded_file is None:
        return existing_image

    ensure_directories()

    original_name = Path(uploaded_file.name)
    suffix = original_name.suffix.lower() or ".jpg"
    filename = f"{recipe_id}{suffix}"
    path = IMAGES_DIR / filename

    if existing_image:
        old_path = ROOT / existing_image
        try:
            old_path.resolve().relative_to(IMAGES_DIR.resolve())
        except ValueError:
            old_path = None

        if old_path and old_path.exists() and old_path != path:
            old_path.unlink()

    path.write_bytes(uploaded_file.getvalue())
    return f"images/recipes/{filename}"
