from pydantic import BaseModel, Field


class AnalysisInput(BaseModel):
    session_id: str
    batch_text: str


class AnalysisOutput(BaseModel):
    idea: str
    details: list[str]
    visual_keywords: list[str] = Field(default_factory=list)
