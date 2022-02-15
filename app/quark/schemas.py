from pydantic import BaseModel

class Error(BaseModel):
    message: str
    field: str
    type: str
    code: int
