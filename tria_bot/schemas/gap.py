from pydantic import BaseModel


class Gap(BaseModel):
    alt: str
    strong: str
    stable: str
    value: float
