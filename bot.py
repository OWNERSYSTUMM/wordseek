import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import BOT_TOKEN, MAX_ATTEMPTS, WORD_LENGTH

# Load words
with open("words.txt", "r") as f:
    WORDS = [w.strip().lower() for w in f if len(w.strip()) == WORD_LENGTH]

# Store game state per chat
games = {}

def generate_feedback(secret, guess):
    result = ""
    for i in range(len(guess)):
        if guess[i] == secret[i]:
            result += "🟢"
        elif guess[i] in secret:
            result += "🟡"
        else:
            result += "⚪"
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    secret = random.choice(WORDS)
    games[chat_id] = {
        "secret": secret,
        "attempts": 0,
    }

    await update.message.reply_text(
        f"🧠 WordSeek 6 Started!\n\nGuess the {WORD_LENGTH}-letter word.\nYou have {MAX_ATTEMPTS} attempts."
    )

async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return

    guess_word = update.message.text.lower().strip()

    if len(guess_word) != WORD_LENGTH:
        return

    game = games[chat_id]
    game["attempts"] += 1

    feedback = generate_feedback(game["secret"], guess_word)

    await update.message.reply_text(feedback)

    if guess_word == game["secret"]:
        await update.message.reply_text("🎉 Correct! You won!")
        del games[chat_id]
        return

    if game["attempts"] >= MAX_ATTEMPTS:
        await update.message.reply_text(
            f"❌ Game Over!\nCorrect word was: {game['secret']}"
        )
        del games[chat_id]

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
