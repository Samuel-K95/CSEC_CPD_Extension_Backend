from app.models import User, Contest, Rating, RatingHistory, Division, UserStatus
from app.crud.users import get_users_by_division 
from sqlalchemy.orm import Session
from app.schemas import attendance_schemas
import math


class Codeforces:
    def __init__(self, db: Session,  ranking: dict, div: Division, attendance: attendance_schemas.AttendanceCreate):
        self.div = div
        self.ranking = ranking
        self.db = db
        self.attendance=attendance
        self.participants = self.build_participant()
        self.PRESENT = []
        self.ABSENT = []
        self.EXCUSED = []
        self.rating_updates = {}
    
    def clean_handle(self, handle):
        if handle.endswith("#"):
            return handle[:-1]
        return handle
    
    def get_user_attendance(self, user_id):
        for record in self.attendance:
            if record.user_id == str(user_id):
                return record.status
        return attendance_schemas.AttendanceStatus.ABSENT

    def build_participant(self):
        division_users = get_users_by_division(db=self.db, division=self.div)
        handle_to_user = {user.codeforces_handle: user for user in division_users}
        participants = []
        
        for rank, entry in enumerate(self.ranking):
            handle = entry.get("handle")
            handle = self.clean_handle(handle=handle)
            user = handle_to_user.get(handle)
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
    

        return participants

    def partition_users(self):
        active_users = [u for u in self.participants if u['status'] == UserStatus.Active]

        self.PRESENT = [u for u in active_users if u['attendance_status'] == attendance_schemas.AttendanceStatus.PRESENT]
        self.ABSENT = [u for u in active_users if u['attendance_status'] == attendance_schemas.AttendanceStatus.ABSENT]
        self.EXCUSED = [u for u in active_users if u['attendance_status'] == attendance_schemas.AttendanceStatus.EXCUSED]

    
    def apply_codeforces_rating(self):
        print("[CF] Applying Codeforces rating update...", flush=True)
        # 3.1 Build contestant structures
        contestants = []
        for user in self.PRESENT:
            # Find the user's standing entry
            standing = next((entry for entry in self.ranking if self.clean_handle(entry['handle']) == user['codeforces_handle']), None)
            if not standing:
                continue
            contestant = {
                'user_id': user['user_id'],
                'rating': user['rating'],
                'rank': int(standing['rank']),
                'points': float(standing.get('score', 0)),
            }
            contestants.append(contestant)
        print(f"[CF] Contestants before ranking: {contestants}", flush=True)

        # 3.2 Assign ranks (with tie handling)
        contestants.sort(key=lambda x: -x['points'])
        prev_points = None
        prev_rank = 0
        for idx, c in enumerate(contestants):
            if prev_points is not None and c['points'] == prev_points:
                c['rank'] = prev_rank
            else:
                c['rank'] = idx + 1
                prev_rank = c['rank']
                prev_points = c['points']
        print(f"[CF] Contestants after tie ranking: {contestants}", flush=True)

        # 3.3 Compute expected seed for each contestant
        def get_seed(contestants, rating):
            seed = 1.0
            for b in contestants:
                seed += 1 / (1 + (10 ** ((b['rating'] - rating) / 400)))
            return seed

        for a in contestants:
            a['seed'] = get_seed([b for b in contestants if b['user_id'] != a['user_id']], a['rating'])
        print(f"[CF] Contestants with seeds: {contestants}", flush=True)

        # 3.4 Compute mid-rank and target rating
        def binary_search_rating(contestants, midRank, eps=1e-5):
            low, high = 1, 8000
            while high - low > eps:
                mid = (low + high) / 2
                seed = get_seed(contestants, mid)
                if seed < midRank:
                    low = mid
                else:
                    high = mid
            return (low + high) / 2

        for a in contestants:
            a['midRank'] = math.sqrt(a['rank'] * a['seed'])
            a['needRating'] = binary_search_rating([b for b in contestants if b['user_id'] != a['user_id']], a['midRank'])
        print(f"[CF] Contestants with needRating: {contestants}", flush=True)

        # 3.5 Compute raw delta
        for a in contestants:   
            a['delta'] = (a['needRating'] - a['rating']) / 2
        print(f"[CF] Contestants with raw delta: {contestants}", flush=True)

        # 3.6 Normalize deltas
        n = len(contestants)
        sum_d = sum(a['delta'] for a in contestants)
        inc1 = -sum_d / n - 1 if n > 0 else 0
        for a in contestants:
            a['delta'] += inc1
        print(f"[CF] Contestants after inc1 normalization: {contestants}", flush=True)

        # top group adjustment
        k = min(int(4 * math.sqrt(n)), n)
        top_k = sorted(contestants, key=lambda x: -x['rating'])[:k]
        sum_top = sum(a['delta'] for a in top_k)
        inc2 = max(min(-sum_top / k, 0), -10) if k > 0 else 0
        for a in contestants:
            a['delta'] += inc2
        print(f"[CF] Contestants after inc2 (top group) normalization: {contestants}", flush=True)

        # 3.7 Validate invariants (optional, print warnings)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if contestants[i]['rating'] > contestants[j]['rating']:
                    if contestants[i]['rating'] + contestants[i]['delta'] < contestants[j]['rating'] + contestants[j]['delta']:
                        print(f"[CF][WARN] Invariant violated: {contestants[i]['user_id']} > {contestants[j]['user_id']} but new_rating <", flush=True)
                if contestants[i]['rating'] < contestants[j]['rating']:
                    if contestants[i]['delta'] < contestants[j]['delta']:
                        print(f"[CF][WARN] Invariant violated: {contestants[i]['user_id']} < {contestants[j]['user_id']} but delta <", flush=True)

        print(f"[CF] Final contestants with deltas: {contestants}", flush=True)
        return contestants 
    
    def aggregate_rating(self, penality):
        for user in self.ABSENT:
            self.rating_updates[user['user_id']] = - penality
        for user in self.EXCUSED:
            self.rating_updates[user['user_id']] = 0
        
        present_updates = self.apply_codeforces_rating()
        for update in present_updates:
            self.rating_updates[update['user_id']] = int(round(update['delta']))
        
        return self.rating_updates
    
    def calculate_final_ratings(self, penality):
        self.partition_users()
        return self.aggregate_rating(penality)







