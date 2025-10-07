from app.db import get_db
from app.models import User, Contest, Rating, RatingHistory, Division
from app.crud.users import get_users_by_division 
from sqlalchemy.orm import Session
from app.schemas import attendance_schemas

class Codeforces:
    def __init__(self, db: Session,  ranking: dict, div: Division, attendance: attendance_schemas.AttendanceCreate):
        print("[DEBUG] Codeforces __init__ called", flush=True)
        self.div = div
        self.ranking = ranking
        self.db = db
        self.attendace=attendance
        self.participant = self.build_participant()
    
    def clean_handle(self, handle):
        if handle.endswith("#"):
            return handle[:-1]
        return handle
    
    def get_user_attendance(self, user_id):
        for record in self.attendace:
            if record.user_id == user_id:
                return record.status
        return attendance_schemas.AttendanceStatus.ABSENT

    def build_participant(self):
        """
        participants: list of all users with attributes:

            - codeforces_handle

            - status ∈ {Active, Terminated, No Longer Active}

            - rating (current rating, default 1500)

            - attendance_status ∈ {Present, Permission, Absent}

            - division (to match contest division)
        """
        print("building participants", flush=True)
        division_users = get_users_by_division(db=self.db, division=self.div)
        handle_to_user = {user.codeforces_handle: user for user in division_users}
        participants = []
        
        print("ranking", self.ranking),
        print("handle_to_user", handle_to_user)
        for rank, entry in enumerate(self.ranking):
            handle = entry.get("handle")
            handle = self.clean_handle(handle=handle)
            print("handle", handle)
            user = handle_to_user.get(handle)
            print(f"hande to user of {handle}", user)
            if not user:
                continue  

            participant_info = {
                "user_id": user.id,
                "codeforces_handle": handle,
                "status": user.status,
                "rating": user.rating,
                "attendance_status": self.get_user_attendance(user.id),
                "division": user.division,
                "rank": rank,
                "problems_solved": entry.get("score", 0),
                "penalty": entry.get("penalty", 0)
            }
            participants.append(participant_info)

        print("participants", participants, len(participants))
        for participant in participants:
            print("participant", participant, flush=True)

        return participants

