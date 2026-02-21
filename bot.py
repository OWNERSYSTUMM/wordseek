import random
import os
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

with open("words.txt", "r") as f:
    WORDS = [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]

games = {}


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
        lines.append(f"{blocks}  {word}")

    return "\n".join(lines)


# START GAME
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in games:
        await update.message.reply_text(
            "There is already a game in progress in this chat. Use /end to end it."
        )
        return

    secret = random.choice(WORDS)

    games[chat_id] = {
        "secret": secret,
        "board": [],
        "guessed": set(),
        "attempts": 0
    }

    await update.message.reply_text("🧠 WordSeek 6 Started!\nGuess the 6-letter word.")


# END GAME
async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        return

    secret = games[chat_id]["secret"]

    await update.message.reply_text(
        f"Game ended. Correct word was: {secret.upper()}"
    )

    del games[chat_id]


# HANDLE GUESS
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        return

    guess_word = update.message.text.lower().strip()

    if len(guess_word) != WORD_LENGTH:
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

    # 🔥 ORIGINAL STYLE: Send new message every guess
    await context.bot.send_message(
        chat_id=chat_id,
        f"{board_text}"
    )

    # WIN
    if guess_word == game["secret"]:
        await update.message.reply_text("🎉 Correct! You won!")
        del games[chat_id]
        return

    # LOSE
    if game["attempts"] >= MAX_ATTEMPTS:
        await update.message.reply_text(
            f"❌ Game Over!\nCorrect word was: {game['secret'].upper()}"
        )
        del games[chat_id]


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("end", end_game))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
