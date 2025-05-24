from pydantic import BaseModel


class Issue(BaseModel):
    id: int
    title: str
    steps: str
    raw_body: str
    labels: list[str]
