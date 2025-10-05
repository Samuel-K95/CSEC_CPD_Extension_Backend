from pydantic import BaseModel
from typing import List, Any
from app.models import AttendanceStatus


class AttendanceBase(BaseModel):
    status: AttendanceStatus

class AttendanceCreate(AttendanceBase):
    user_id: str
    contest_id : str
    status: AttendanceStatus

class AttendanceRead(AttendanceBase):
    id: str
    user_id: str
    contest_id: str

class SubmitAttendanceRequest(BaseModel):
    attendance: List[AttendanceCreate]
    ranking_data: List[dict]

