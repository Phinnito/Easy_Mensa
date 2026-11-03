from collections import Counter

from src.services.storage_service import list_recipes


def get_ingredient_usage() -> Counter[str]:
    usage: Counter[str] = Counter()

    for recipe in list_recipes():
        for ingredient in recipe.ingredients:
            usage[ingredient.name.strip()] += 1

            for substitute in ingredient.substitutes:
                usage[substitute.name.strip()] += 1

    return usage


def get_ingredient_options() -> list[str]:
    """All primary and substitute ingredients, most-used first."""
    usage = get_ingredient_usage()
    return [name for name, _count in usage.most_common()]


def get_ingredient_recipe_counts() -> dict[str, int]:
    """Number of recipes in which each ingredient or substitute appears."""
    counts: Counter[str] = Counter()

    for recipe in list_recipes():
        seen: set[str] = set()

        for ingredient in recipe.ingredients:
            seen.add(ingredient.name.strip())
            seen.update(
                substitute.name.strip()
                for substitute in ingredient.substitutes
            )

        counts.update(seen)

    return dict(counts)
