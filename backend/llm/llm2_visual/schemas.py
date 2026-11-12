from pydantic import BaseModel


class VisualQueryInput(BaseModel):
    idea: str
    details: list[str]


class VisualQueryOutput(BaseModel):
    query: str
