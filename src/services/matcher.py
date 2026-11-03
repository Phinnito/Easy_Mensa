from src.models.recipe import Recipe


QUALITY_RANK = {
    "close": 0,
    "acceptable": 1,
    "noticeable_difference": 2,
}


def _normalize(values: list[str] | set[str]) -> set[str]:
    return {value.strip().casefold() for value in values if value.strip()}


def match_recipe(recipe: Recipe, available: list[str] | set[str]) -> dict:
    available_normalized = _normalize(available)

    missing_required: list[str] = []
    missing_recommended: list[str] = []
    substitutions: list[dict] = []

    for ingredient in recipe.ingredients:
        primary = ingredient.name.strip()
        primary_key = primary.casefold()

        if primary_key in available_normalized:
            continue

        matches = [
            substitute
            for substitute in ingredient.substitutes
            if substitute.name.strip().casefold() in available_normalized
        ]

        if matches:
            best = sorted(
                matches,
                key=lambda item: QUALITY_RANK[item.quality],
            )[0]
            substitutions.append(
                {
                    "original": primary,
                    "substitute": best.name,
                    "quality": best.quality,
                    "note": best.note,
                    "importance": ingredient.importance,
                }
            )
            continue

        if ingredient.importance == "required":
            missing_required.append(primary)
        elif ingredient.importance == "recommended":
            missing_recommended.append(primary)

    cookable = not missing_required

    if not cookable:
        status = "missing_required"
    elif any(
        item["quality"] == "noticeable_difference"
        for item in substitutions
    ):
        status = "compromise"
    elif substitutions:
        status = "substitution"
    elif missing_recommended:
        status = "good"
    else:
        status = "excellent"

    penalty = (
        len(missing_required) * 40
        + len(missing_recommended) * 7
        + sum(
            {
                "close": 2,
                "acceptable": 7,
                "noticeable_difference": 15,
            }[item["quality"]]
            for item in substitutions
        )
    )

    return {
        "cookable": cookable,
        "status": status,
        "score": max(0, 100 - penalty),
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "substitutions": substitutions,
    }
