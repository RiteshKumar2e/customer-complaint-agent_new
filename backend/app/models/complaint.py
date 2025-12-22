from pydantic import BaseModel


class ComplaintRequest(BaseModel):
    complaint: str


class ComplaintResponse(BaseModel):
    category: str
    priority: str
    response: str
    action: str
