from pydantic import BaseModel


class SOffer(BaseModel):
    id: int
    name: str
