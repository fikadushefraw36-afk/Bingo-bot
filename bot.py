import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database
from game import BingoGame
from bank import BankSystem

# ከRailway Environment Variable ላይ ቶከኑን ማንበብ
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

games = {}
db = Database()
bank = BankSystem()

async def start(update: Update, context):
    user = update.effective_user
    db.add_user(user.id, user.username)
    bank.create_account(user.id, user.username)
    await update.message.reply_text(
        "🔴 ወደ ቢንጎ ቦት እንኳን በደህና መጡ! 🔴\n\n"
        "💰 /balance - ሂሳብ ማየት\n"
        "💸 /deposit ብር - ገንዘብ ማስገባት\n"
        "🎮 /newgame - አዲስ ጨዋታ መጀመር\n"
        "🃟 /buycards - ካርድ መግዛት\n"
        "🎲 /call - ቁጥር መጥራት\n"
        "🏆 /leaderboard - ከፍተኛ አሸናፊዎች"
    )

async def balance(update: Update, context):
    bal = bank.get_balance(update.effective_user.id)
    await update.message.reply_text(f"💰 ሂሳብዎ: *{bal} ብር*", parse_mode='Markdown')

async def deposit(update: Update, context):
    args = context.args
    if not args:
        await update.message.reply_text("ምሳሌ: /deposit 100")
        return
    try:
        amount = int(args[0])
        success, msg = bank.deposit(update.effective_user.id, amount)
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("ትክክለኛ ቁጥር ያስገቡ!")

async def newgame(update: Update, context):
    chat_id = update.effective_chat.id
    if chat_id in games and games[chat_id].active:
        await update.message.reply_text("ጨዋታ ቀድሞውኑ እየተካሄደ ነው!")
        return
    games[chat_id] = BingoGame()
    games[chat_id].create_game(chat_id)
    keyboard = [[InlineKeyboardButton("🔴 ቀላቀል", callback_data='join')]]
    await update.message.reply_text("አዲስ ቢንጎ ጨዋታ ተጀምሯል!", reply_markup=InlineKeyboardMarkup(keyboard))

async def join_game(update: Update, context):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user = query.from_user
    if chat_id not in games:
        await query.edit_message_text("ምንም ጨዋታ የለም")
        return
    await query.edit_message_text(f"✅ {user.first_name} ተቀላቀለ! /buycards በመጠቀም ካርድ ይግዙ")

async def buycards(update: Update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    args = context.args
    if chat_id not in games:
        await update.message.reply_text("ምንም ንቁ ጨዋታ የለም!")
        return
    num_cards = int(args[0]) if args and args[0].isdigit() else 1
    num_cards = min(num_cards, 10)
    total_cost = num_cards * 10
    if bank.get_balance(user_id) < total_cost:
        await update.message.reply_text(f"በቂ ገንዘብ የለም! ያለዎት: {bank.get_balance(user_id)} ብር")
        return
    bank.withdraw(user_id, total_cost)
    success, bought = games[chat_id].add_player(user_id, update.effective_user.username, num_cards)
    if success:
        await update.message.reply_text(f"✅ {bought} ካርድ ገዝተዋል! ወጪ: {total_cost} ብር")
    else:
        await update.message.reply_text("ካርድ መግዛት አልተቻለም!")

async def call(update: Update, context):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("ምንም ንቁ ጨዋታ የለም!")
        return
    number, winner_info = games[chat_id].call_number()
    if number:
        msg = f"🔴 ቁጥር {number} ተጠራ!"
        if winner_info:
            winner_id, cards = winner_info
            prize = 200
            bank.add_winnings(winner_id, prize)
            msg += f"\n🎉 ቢንጎ! አሸናፊው {games[chat_id].players[winner_id]['username']} ነው! 🎉\n🏆 ሽልማት: {prize} ብር"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("ሁሉም ቁጥሮች ተጠርተዋል!")

async def leaderboard(update: Update, context):
    leaders = db.get_leaderboard()
    msg = "🏆 ከፍተኛ አሸናፊዎች:\n"
    for i, (name, wins) in enumerate(leaders[:10], 1):
        msg += f"{i}. {name or 'አልታወቀም'}: {wins} ድል\n"
    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("newgame", newgame))
    app.add_handler(CommandHandler("buycards", buycards))
    app.add_handler(CommandHandler("call", call))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(join_game, pattern='join'))
    print("🔴 ቢንጎ ቦት ተጀምሯል!")
    app.run_polling()

if __name__ == "__main__":
    main()
