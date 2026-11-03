from pydantic import BaseModel, Field


class IngredientKnowledge(BaseModel):
    id: str = Field(min_length=1)
    ingredient: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)

    summary: str = ""
    function: str = ""
    how_to_use: str = ""
    how_to_choose: str = ""
    storage: str = ""

    mistakes: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
