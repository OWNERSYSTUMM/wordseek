import random
import os
import json
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

# 🔥 Leaderboard import
from leaderboard import (
    add_points,
    get_global_top,
    get_group_top,
    get_today_top,
    get_week_top,
    get_month_top,
    get_all_time_top
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

WORD_LENGTH = 6
BASE_POINTS = 30

# Load word list
with open("words.txt", "r") as f:
    WORDS = [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]

# Load dictionary
with open("dictionary.json", "r") as f:
    DICTIONARY = json.load(f)

games = {}


# 🟩🟨🟥 Feedback
def generate_feedback(secret, guess):
    feedback = ["🔴"] * WORD_LENGTH
    secret_temp = list(secret)

    for i in range(WORD_LENGTH):
        if guess[i] == secret[i]:
            feedback[i] = "🟢"
            secret_temp[i] = None

    for i in range(WORD_LENGTH):
        if feedback[i] == "🔴" and guess[i] in secret_temp:
            feedback[i] = "🟡"
            secret_temp[secret_temp.index(guess[i])] = None

    return feedback


def build_board(board):
    lines = []
    for row in board:
        blocks = " ".join(row["feedback"])
        word = row["word"]
        lines.append(f"{blocks}   {word}")
    return "\n".join(lines)


# 🎯 NEW GAME
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in games:
        await context.bot.send_message(
            chat_id=chat_id,
            text="There is already a game in progress. Use /end to stop it."
        )
        return

    secret = random.choice(WORDS)

    games[chat_id] = {
        "secret": secret,
        "board": [],
        "guessed": set(),
        "wrong_count": 0,
        "current_points": float(BASE_POINTS),
    }

    await context.bot.send_message(
        chat_id=chat_id,
        text="Game started! Guess the 6 letter word!"
    )


# ❌ END GAME
async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        return

    secret = games[chat_id]["secret"]
    entry = DICTIONARY.get(secret, {})
    meaning = entry.get("meaning")

    message = (
        "<blockquote>"
        "🎮 Game Ended"
        "</blockquote>\n\n"

        "<blockquote>"
        f"Correct Word: {secret}\n"
    )

    if meaning:
        message += f"Meaning: {meaning}\n"

    message += "</blockquote>\nStart a new game with /new"

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="HTML"
    )

    del games[chat_id]

# 🎮 GUESS
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        return

    guess_word = update.message.text.lower().strip()

    if len(guess_word) != WORD_LENGTH:
        return

    if guess_word not in WORDS:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"{guess_word} is not a valid word."
        )
        return

    game = games[chat_id]

    if guess_word in game["guessed"]:
        await context.bot.send_message(
            chat_id=chat_id,
            "Someone has already guessed your word. Please try another one!"
        )
        return

    game["guessed"].add(guess_word)

    feedback = generate_feedback(game["secret"], guess_word)

    game["board"].append({
        "feedback": feedback,
        "word": guess_word.upper()
    })

    # ❌ Silent penalty
    if guess_word != game["secret"]:
        game["wrong_count"] += 1
        if game["wrong_count"] % 2 == 0:
            game["current_points"] -= 0.5
            game["current_points"] = max(0, game["current_points"])

    board_text = build_board(game["board"])

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"{board_text}"
    )

    # ✅ WIN
    if guess_word == game["secret"]:
        user_id = str(update.effective_user.id)
        username = update.effective_user.first_name
        earned = round(game["current_points"], 2)

        # 🔥 Mongo Save
        add_points(user_id, username, earned, str(chat_id))

        word = game["secret"]
        entry = DICTIONARY.get(word, {})
        pronunciation = entry.get("pronunciation")
        meaning = entry.get("meaning")

        message = (
            f"Congrats! You guessed it correctly.\n"
            f"Added {earned} to the leaderboard.\n"
            f"Start with /new\n\n"
            f"Correct Word: {word}"
        )

        if pronunciation:
            message += f"\n{word.capitalize()} {pronunciation}"

        if meaning:
            message += f"\nMeaning: {meaning}"

        await update.message.reply_text(message)

        del games[chat_id]


# 🏆 LEADERBOARD MENU
async def leaderboard_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🌍 Global", callback_data="lb_global"),
            InlineKeyboardButton("👥 This Chat", callback_data="lb_group"),
        ],
        [
            InlineKeyboardButton("📅 Today", callback_data="lb_today"),
            InlineKeyboardButton("📆 This Week", callback_data="lb_week"),
        ],
        [
            InlineKeyboardButton("🗓 This Month", callback_data="lb_month"),
            InlineKeyboardButton("📊 All Time", callback_data="lb_all"),
        ],
    ]

    await update.message.reply_text(
        "🏆 Select Leaderboard Type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# 🔥 CALLBACK HANDLER
async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = str(query.message.chat.id)
    data = query.data

    if data == "lb_global":
        users = get_global_top()
        title = "🌍 Global Leaderboard"

    elif data == "lb_group":
        users = get_group_top(chat_id)
        title = "👥 Group Leaderboard"

    elif data == "lb_today":
        users = get_today_top()
        title = "📅 Today's Leaderboard"

    elif data == "lb_week":
        users = get_week_top()
        title = "📆 This Week Leaderboard"

    elif data == "lb_month":
        users = get_month_top()
        title = "🗓 This Month Leaderboard"

    else:
        users = get_all_time_top()
        title = "📊 All Time Leaderboard"

    text = f"🏆 {title}\n\n"

    rank = 1
    for user in users:
        if isinstance(user, tuple):
            name, pts = user
        else:
            name = user.get("username", "User")
            pts = user.get("global_points", 0)

            if data == "lb_group":
                pts = user.get("groups", {}).get(chat_id, 0)

        if pts > 0:
            text += f"{rank}. {name} — {round(pts,2)} pts\n"
            rank += 1

    await query.edit_message_text(text)


# 🚀 MAIN
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("end", end_game))
    app.add_handler(CommandHandler("leaderboard", leaderboard_menu))
    app.add_handler(CallbackQueryHandler(leaderboard_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
