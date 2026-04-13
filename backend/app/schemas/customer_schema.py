from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CustomerBase(BaseModel):
    entry_time: datetime
    tracker_id: int

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    exit_time: Optional[datetime] = None
    visit_duration: Optional[int] = None

    class Config:   # ✅ fixed
        from_attributes = True