import random
import os
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

WORD_LENGTH = 6
MAX_ATTEMPTS = 6

# Load word list
with open("words.txt", "r") as f:
    WORDS = [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]

# Load dictionary
with open("dictionary.json", "r") as f:
    DICTIONARY = json.load(f)

games = {}
leaderboard = {}


def generate_feedback(secret, guess):
    feedback = ["🟥"] * WORD_LENGTH
    secret_temp = list(secret)

    # Green pass
    for i in range(WORD_LENGTH):
        if guess[i] == secret[i]:
            feedback[i] = "🟩"
            secret_temp[i] = None

    # Yellow pass
    for i in range(WORD_LENGTH):
        if feedback[i] == "🟥" and guess[i] in secret_temp:
            feedback[i] = "🟨"
            secret_temp[secret_temp.index(guess[i])] = None

    return feedback


def build_board(board):
    lines = []
    for row in board:
        blocks = " ".join(row["feedback"])
        word = row["word"]
        lines.append(f"{blocks}   {word}")
    return "\n".join(lines)


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
        "attempts": 0
    }

    await context.bot.send_message(
        chat_id=chat_id,
        text="🧠 WordSeek 6 Started!\nGuess the 6-letter word."
    )


async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        return

    secret = games[chat_id]["secret"]

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Game ended. Correct word was: {secret.upper()}"
    )

    del games[chat_id]


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
        return

    game["guessed"].add(guess_word)
    game["attempts"] += 1

    feedback = generate_feedback(game["secret"], guess_word)

    game["board"].append({
        "feedback": feedback,
        "word": guess_word.upper()
    })

    board_text = build_board(game["board"])

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"WordSeek\n{board_text}"
    )

    # WIN
    if guess_word == game["secret"]:
        winner = update.effective_user.first_name
        attempts = game["attempts"]

        points = (MAX_ATTEMPTS - attempts + 1) * 2
        leaderboard[winner] = leaderboard.get(winner, 0) + points

        word = game["secret"]
        data = DICTIONARY.get(word, {})
        pronunciation = data.get("pronunciation", "")
        meaning = data.get("meaning", "Meaning not available.")

        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🎉 Congrats {winner}! You guessed it correctly.\n"
                f"Added {points} to the leaderboard.\n"
                f"Start with /new\n\n"
                f"📖 Correct Word: {word}\n"
                f"{word.capitalize()} {pronunciation}\n\n"
                f"Meaning:\n{meaning}"
            )
        )

        del games[chat_id]
        return

    # LOSE
    if game["attempts"] >= MAX_ATTEMPTS:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Game Over!\nCorrect word was: {game['secret'].upper()}"
        )
        del games[chat_id]


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not leaderboard:
        await update.message.reply_text("Leaderboard is empty.")
        return

    sorted_board = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 Leaderboard:\n\n"
    for name, score in sorted_board:
        text += f"{name}: {score}\n"

    await update.message.reply_text(text)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("end", end_game))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
