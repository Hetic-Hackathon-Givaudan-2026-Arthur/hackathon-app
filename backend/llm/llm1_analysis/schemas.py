from pydantic import BaseModel


class AnalysisInput(BaseModel):
    session_id: str
    batch_text: str


class AnalysisOutput(BaseModel):
    idea: str
    details: list[str]
