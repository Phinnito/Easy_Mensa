import hashlib
import json
from pathlib import Path

from src.models.knowledge import IngredientKnowledge


ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT / "data" / "knowledge"


def ensure_knowledge_directory() -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


def knowledge_id_for_ingredient(ingredient: str) -> str:
    normalized = ingredient.strip().casefold().encode("utf-8")
    digest = hashlib.sha1(normalized).hexdigest()[:12]
    return f"ingredient-{digest}"


def knowledge_path(knowledge_id: str) -> Path:
    return KNOWLEDGE_DIR / f"{knowledge_id}.json"


def load_knowledge(path: Path) -> IngredientKnowledge:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return IngredientKnowledge.model_validate(raw)


def list_knowledge() -> list[IngredientKnowledge]:
    ensure_knowledge_directory()
    items: list[IngredientKnowledge] = []

    for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        try:
            items.append(load_knowledge(path))
        except (OSError, json.JSONDecodeError, ValueError):
            continue

    return items


def knowledge_map() -> dict[str, IngredientKnowledge]:
    return {
        item.ingredient.strip().casefold(): item
        for item in list_knowledge()
    }


def get_knowledge_for_ingredient(ingredient: str) -> IngredientKnowledge | None:
    return knowledge_map().get(ingredient.strip().casefold())


def save_knowledge(item: IngredientKnowledge) -> Path:
    ensure_knowledge_directory()
    path = knowledge_path(item.id)
    path.write_text(
        json.dumps(
            item.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path
