from pydantic import BaseModel
from typing import List


class PullRequest(BaseModel):
    id: int
    title: str
    test: str
    explaination: str
    files: List[str]
