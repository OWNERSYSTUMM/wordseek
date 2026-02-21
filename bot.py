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

# Load token
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

WORD_LENGTH = 6
MAX_ATTEMPTS = 6

# Load words
with open("words6.txt", "r") as f:
    WORDS = [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]

# Game storage
games = {}


# Wordle logic
def generate_feedback(secret, guess):
    feedback = ["⬜"] * len(secret)
    secret_temp = list(secret)

    # Green pass
    for i in range(len(secret)):
        if guess[i] == secret[i]:
            feedback[i] = "🟩"
            secret_temp[i] = None

    # Yellow pass
    for i in range(len(secret)):
        if feedback[i] == "⬜":
            if guess[i] in secret_temp:
                feedback[i] = "🟨"
                secret_temp[secret_temp.index(guess[i])] = None
            else:
                feedback[i] = "🟥"

    return " ".join(feedback)


# NEW GAME
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in games:
        await update.message.reply_text(
            "⚠️ There is already a game in progress.\nUse /end to end it."
        )
        return

    secret = random.choice(WORDS)

    msg = await update.message.reply_text(
        "🧠 WordSeek 6 Started!\n\nGuess the 6-letter word."
    )

    games[chat_id] = {
        "secret": secret,
        "attempts": 0,
        "board": [],
        "guessed_words": set(),
        "message_id": msg.message_id
    }


# END GAME
async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        return

    secret = games[chat_id]["secret"]

    await update.message.reply_text(
        f"❌ Game Ended!\nCorrect word was: {secret.upper()}"
    )

    del games[chat_id]


# HANDLE GUESSES
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        return

    guess_word = update.message.text.lower().strip()

    if len(guess_word) != WORD_LENGTH:
        return

    game = games[chat_id]

    # Prevent repeat guess
    if guess_word in game["guessed_words"]:
        await update.message.reply_text("⚠️ Already tried this word!")
        return

    game["guessed_words"].add(guess_word)
    game["attempts"] += 1

    feedback = generate_feedback(game["secret"], guess_word)

    game["board"].append(f"{feedback}   {guess_word.upper()}")

    board_text = "\n".join(game["board"])

    # Edit same message
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=game["message_id"],
        text=f"🧠 WordSeek 6\n\n{board_text}"
    )

    # Win
    if guess_word == game["secret"]:
        await update.message.reply_text("🎉 Correct! You won!")
        del games[chat_id]
        return

    # Lose
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
