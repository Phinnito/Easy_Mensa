from typing import Literal

from pydantic import BaseModel, Field


Cuisine = Literal[
    "中餐",
    "西餐",
    "南美菜",
    "东亚菜",
    "东南亚菜",
    "南亚菜",
    "非洲菜",
]

Scenario = Literal[
    "聚会菜谱",
    "精致一人食",
    "随便吃点",
    "两个人吃",
    "认真做饭",
]

Importance = Literal["required", "recommended", "optional"]

ReplacementQuality = Literal[
    "close",
    "acceptable",
    "noticeable_difference",
]


class Substitute(BaseModel):
    name: str = Field(min_length=1)
    quality: ReplacementQuality
    note: str = ""


class Ingredient(BaseModel):
    name: str = Field(min_length=1)
    amount: str = ""
    importance: Importance
    substitutes: list[Substitute] = Field(default_factory=list)


class Recipe(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    cuisine: Cuisine

    difficulty: int = Field(ge=1, le=5)
    ingredient_complexity: int = Field(ge=1, le=5)
    shareability: int = Field(ge=1, le=5)

    time_minutes: int = Field(gt=0)
    servings: int = Field(gt=0)

    scenarios: list[Scenario] = Field(default_factory=list)

    image: str | None = None
    ingredients: list[Ingredient] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)
    tips: list[str] = Field(default_factory=list)
