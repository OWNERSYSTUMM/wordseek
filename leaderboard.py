import os
from datetime import datetime, timedelta
import pytz
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["wordseek"]
users_col = db["leaderboard"]

# Indian Standard Time
IST = pytz.timezone("Asia/Kolkata")


# 🔥 Add points (Global + Group + History)
def add_points(user_id: str, username: str, points: float, chat_id: str):
    users_col.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "global_points": points,
                f"groups.{chat_id}": points
            },
            "$set": {"username": username},
            "$push": {
                "history": {
                    "points": points,
                    "chat_id": chat_id,
                    "timestamp": datetime.now(IST)
                }
            }
        },
        upsert=True
    )


# 🌍 Global Leaderboard
def get_global_top(limit=10):
    return list(
        users_col.find().sort("global_points", -1).limit(limit)
    )


# 👥 Group Leaderboard
def get_group_top(chat_id: str, limit=10):
    return list(
        users_col.find().sort(f"groups.{chat_id}", -1).limit(limit)
    )


# 📅 Today Leaderboard (IST)
def get_today_top(limit=10):
    now = datetime.now(IST)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    users = users_col.find({
        "history.timestamp": {"$gte": start_of_day}
    })

    scores = {}

    for user in users:
        total = 0
        for h in user.get("history", []):
            if h["timestamp"] >= start_of_day:
                total += h["points"]

        if total > 0:
            scores[user["username"]] = total

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return sorted_scores[:limit]


# 📆 This Week Leaderboard (IST)
def get_week_top(limit=10):
    now = datetime.now(IST)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    users = users_col.find({
        "history.timestamp": {"$gte": start_of_week}
    })

    scores = {}

    for user in users:
        total = 0
        for h in user.get("history", []):
            if h["timestamp"] >= start_of_week:
                total += h["points"]

        if total > 0:
            scores[user["username"]] = total

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return sorted_scores[:limit]


# 🗓 This Month Leaderboard (IST)
def get_month_top(limit=10):
    now = datetime.now(IST)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    users = users_col.find({
        "history.timestamp": {"$gte": start_of_month}
    })

    scores = {}

    for user in users:
        total = 0
        for h in user.get("history", []):
            if h["timestamp"] >= start_of_month:
                total += h["points"]

        if total > 0:
            scores[user["username"]] = total

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return sorted_scores[:limit]


# 📊 All Time (same as global but formatted)
def get_all_time_top(limit=10):
    return get_global_top(limit)
