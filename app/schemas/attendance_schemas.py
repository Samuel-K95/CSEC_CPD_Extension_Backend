from pydantic import BaseModel

from app.models import AttendanceStatus


class AttendanceBase(BaseModel):
    status: AttendanceStatus

class AttendanceCreate(AttendanceBase):
    user_id: str
    contest_id : str

class AttendanceRead(AttendanceBase):
    id: str
    user_id: str
    contest_id: str

