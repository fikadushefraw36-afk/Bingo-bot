import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database
from game import BingoGame
from bank import BankSystem

# ሎግ ለማየት
logging.basicConfig(level=logging.INFO)

# ከRailway Environment Variable ላይ ቶከኑን ማንበብ
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not found! Please add it in Railway Variables.")
    exit(1)

print("✅ BOT_TOKEN found!")

# ግሎባል ተለዋዋጮች
games = {}
db = Database()
bank = BankSystem()

# ==================== ትዕዛዞች ====================

async def start(update: Update, context):
    """መጀመሪያ ትዕዛዝ - አዲስ ተጠቃሚ ሲመዘገብ 10 ብር ቦነስ ይሰጣል"""
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    # ተጠቃሚ ማስመዝገብ
    db.add_user(user_id, username)
    bank.create_account(user_id, username)
    
    # ቦነስ መስጠት
    bonus_msg = ""
    success, bonus_result = bank.add_bonus(user_id)
    if success:
        bonus_msg = f"\n\n🎁 *{bonus_result}* 🎁"
    
    await update.message.reply_text(
        f"🔴 *ወደ ቢንጎ ቦት እንኳን በደህና መጡ!* 🔴\n\n"
        f"💰 /balance - ሂሳብ ማየት\n"
        f"💸 /deposit <ብር> - ገንዘብ ማስገባት\n"
        f"🎮 /newgame - አዲስ ጨዋታ መጀመር\n"
        f"🃟 /buycards <ካርድ_ብዛት> - ካርድ መግዛት\n"
        f"🎲 /call - ቁጥር መጥራት\n"
        f"🏆 /leaderboard - ከፍተኛ አሸናፊዎች\n"
        f"📊 /stats - ጨዋታ ሁኔታ\n"
        f"📜 /history - ግብይት ታሪክ{bonus_msg}",
        parse_mode='Markdown'
    )

async def balance(update: Update, context):
    """ሂሳብ ማየት"""
    user_id = update.effective_user.id
    bal = bank.get_balance(user_id)
    await update.message.reply_text(f"💰 *ሂሳብዎ*: {bal} ብር", parse_mode='Markdown')

async def deposit(update: Update, context):
    """ገንዘብ ማስገባት"""
    args = context.args
    if not args:
        await update.message.reply_text("📝 *ምሳሌ:* /deposit 100\n\nበ10 ብር እና በላይ ማስገባት ይቻላል", parse_mode='Markdown')
        return
    try:
        amount = int(args[0])
        if amount <= 0:
            await update.message.reply_text("❌ እባክዎ ከ0 በላይ ቁጥር ያስገቡ!")
            return
        success, msg = bank.deposit(update.effective_user.id, amount)
        await update.message.reply_text(f"{'✅' if success else '❌'} {msg}")
    except ValueError:
        await update.message.reply_text("❌ እባክዎ ትክክለኛ ቁጥር ያስገቡ!")

async def withdraw(update: Update, context):
    """ገንዘብ ማውጣት"""
    args = context.args
    if not args:
        await update.message.reply_text("📝 *ምሳሌ:* /withdraw 50", parse_mode='Markdown')
        return
    try:
        amount = int(args[0])
        if amount <= 0:
            await update.message.reply_text("❌ እባክዎ ከ0 በላይ ቁጥር ያስገቡ!")
            return
        success, msg = bank.withdraw(update.effective_user.id, amount)
        await update.message.reply_text(f"{'✅' if success else '❌'} {msg}")
    except ValueError:
        await update.message.reply_text("❌ እባክዎ ትክክለኛ ቁጥር ያስገቡ!")

async def newgame(update: Update, context):
    """አዲስ ጨዋታ መጀመር"""
    chat_id = update.effective_chat.id
    
    if chat_id in games and games[chat_id].active:
        await update.message.reply_text("🔴 ጨዋታ ቀድሞውኑ እየተካሄደ ነው!")
        return
    
    games[chat_id] = BingoGame()
    games[chat_id].create_game(chat_id)
    
    keyboard = [[InlineKeyboardButton("🔴 ቀላቀል", callback_data='join')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎲 *አዲስ ቢንጎ ጨዋታ ተጀምሯል!* 🎲\n\n"
        "ተጫዋቾች እንዲቀላቀሉ ይጠብቁ...\n"
        "ከዚያ /buycards በመጠቀም ካርድ ይግዙ",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def join_game(update: Update, context):
    """ጨዋታ መቀላቀል (ከኢንላይን ቁልፍ)"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    user = query.from_user
    
    if chat_id not in games:
        await query.edit_message_text("🔴 ምንም ንቁ ጨዋታ የለም! /newgame ይጠቀሙ")
        return
    
    if not games[chat_id].active:
        await query.edit_message_text("🔴 ጨዋታው ተጠናቋል! /newgame ይጠቀሙ")
        return
    
    await query.edit_message_text(f"✅ *{user.first_name}* ጨዋታውን ተቀላቀለ!\n\n🃟 /buycards በመጠቀም ካርድ ይግዙ", parse_mode='Markdown')

async def buycards(update: Update, context):
    """ካርድ መግዛት - 1 ካርድ = 10 ብር"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    args = context.args
    
    if chat_id not in games:
        await update.message.reply_text("🔴 ምንም ንቁ ጨዋታ የለም! /newgame ይጠቀሙ")
        return
    
    if not games[chat_id].active:
        await update.message.reply_text("🔴 ጨዋታው ተጠናቋል! /newgame ይጠቀሙ")
        return
    
    num_cards = 1
    if args and args[0].isdigit():
        num_cards = min(int(args[0]), 10)
    
    total_cost = num_cards * 10
    
    if bank.get_balance(user_id) < total_cost:
        await update.message.reply_text(
            f"❌ *በቂ ገንዘብ የለም!*\n\n"
            f"💰 ያለዎት: {bank.get_balance(user_id)} ብር\n"
            f"🃟 የሚፈለጉት: {num_cards} ካርድ(ዎች)\n"
            f"💵 ወጪ: {total_cost} ብር\n\n"
            f"/deposit በመጠቀም ገንዘብ ያስገቡ",
            parse_mode='Markdown'
        )
        return
    
    bank.withdraw(user_id, total_cost, f"BUY_{num_cards}_CARDS")
    
    game = games[chat_id]
    success, bought = game.add_player(user_id, update.effective_user.username, num_cards)
    
    if success:
        await update.message.reply_text(
            f"✅ *{bought} ካርድ(ዎች) ተገዝተዋል!*\n"
            f"💵 ወጪ: {total_cost} ብር\n"
            f"💰 ቀሪ ሂሳብ: {bank.get_balance(user_id)} ብር\n\n"
            f"🃟 /cards - ካርዶችዎን ለማየት\n"
            f"🎲 /call - ቁጥር ለመጥራት",
            parse_mode='Markdown'
        )
    else:
        bank.deposit(user_id, total_cost, "REFUND")
        await update.message.reply_text("🔴 ካርድ መግዛት አልተቻለም! እባክዎ እንደገና ይሞክሩ")

async def cards(update: Update, context):
    """የተጫዋቹን ካርዶች ማሳየት"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in games:
        await update.message.reply_text("🔴 ምንም ጨዋታ የለም")
        return
    
    result = games[chat_id].format_cards(user_id)
    if result:
        await update.message.reply_text(result, parse_mode='Markdown')
    else:
        await update.message.reply_text("🔴 እስካሁን ካርድ አልገዙም! /buycards ይጠቀሙ")

async def call(update: Update, context):
    """ቁጥር መጥራት እና አሸናፊ መፈለግ"""
    chat_id = update.effective_chat.id
    
    if chat_id not in games:
        await update.message.reply_text("🔴 ምንም ንቁ ጨዋታ የለም! /newgame ይጠቀሙ")
        return
    
    game = games[chat_id]
    
    if not game.active:
        await update.message.reply_text("🔴 ጨዋታው አልተጀመረም ወይም ተጠናቋል!")
        return
    
    if len(game.players) == 0:
        await update.message.reply_text("🔴 ምንም ተጫዋቾች የሉም! በመጀመሪያ /buycards ይጠቀሙ")
        return
    
    result = game.call_number()
    
    if result:
        number, winner_info = result
        msg = f"🔴 *ቁጥር {number} ተጠራ!* 🔴"
        
        if winner_info:
            winner_id, num_cards = winner_info
            winner_name = game.players[winner_id]['username']
            prize = 200
            
            bank.add_winnings(winner_id, prize)
            
            msg += f"\n\n🎉 *ቢንጎ!* 🎉\n"
            msg += f"🏆 አሸናፊ: *{winner_name}*\n"
            msg += f"🃟 በ{num_cards} ካርድ(ዎች) አሸንፏል!\n"
            msg += f"💰 ሽልማት: *{prize} ብር*"
            
            game.active = False
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("🔴 ሁሉም ቁጥሮች ተጠርተዋል ወይም ስህተት ተፈጥሯል!")

async def leaderboard(update: Update, context):
    """ከፍተኛ አሸናፊዎች ማሳየት"""
    leaders = db.get_leaderboard()
    
    if not leaders:
        await update.message.reply_text("📭 እስካሁን ምንም አሸናፊ የለም!")
        return
    
    msg = "🏆 *ከፍተኛ አሸናፊዎች* 🏆\n\n"
    for i, (username, wins) in enumerate(leaders[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        msg += f"{medal} {i}. {username or 'አልታወቀም'}: *{wins}* ድል(ዎች)\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def history(update: Update, context):
    """የግብይት ታሪክ ማሳየት"""
    user_id = update.effective_user.id
    transactions = bank.get_transaction_history(user_id, 10)
    
    if not transactions:
        await update.message.reply_text("📭 ምንም ግብይት የለም!")
        return
    
    msg = "📜 *የግብይት ታሪክ* 📜\n\n"
    for t in transactions:
        type_emoji = {
            'deposit': '💰',
            'withdraw': '💸',
            'winning': '🏆',
            'bonus': '🎁'
        }.get(t[0], '📝')
        
        msg += f"{type_emoji} {t[0].upper()}: {t[1]} ብር\n"
        msg += f"   🕐 {t[3][:16]}\n\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def stats(update: Update, context):
    """የጨዋታ ሁኔታ ማሳየት"""
    chat_id = update.effective_chat.id
    
    if chat_id not in games:
        await update.message.reply_text("🔴 ምንም ንቁ ጨዋታ የለም!")
        return
    
    game = games[chat_id]
    stats_data = game.get_game_stats()
    
    msg = f"📊 *የጨዋታ ሁኔታ* 📊\n\n"
    msg += f"👥 ተጫዋቾች: {stats_data['total_players']}\n"
    msg += f"🃟 የተሸጡ ካርዶች: {stats_data['total_cards_sold']}/200\n"
    msg += f"🎫 የቀሩ ካርዶች: {stats_data['remaining_cards']}\n"
    msg += f"🎯 ንቁ ተጫዋቾች: {stats_data['active_players']}\n"
    msg += f"🔢 የተጠሩ ቁጥሮች: {stats_data['called_numbers']}/75"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def summary(update: Update, context):
    """የሂሳብ ማጠቃለያ"""
    user_id = update.effective_user.id
    acc_summary = bank.get_account_summary(user_id)
    
    if not acc_summary:
        await update.message.reply_text("🔴 ሂሳብ አልተገኘም! /start ይጠቀሙ")
        return
    
    msg = f"📊 *የሂሳብ ማጠቃለያ*\n\n"
    msg += f"💰 ቀሪ ሂሳብ: *{acc_summary['balance']} ብር*\n"
    msg += f"📥 ጠቅላላ ገቢ: {acc_summary['total_deposited']} ብር\n"
    msg += f"📤 ጠቅላላ ወጪ: {acc_summary['total_withdrawn']} ብር\n"
    msg += f"🏆 ከጨዋታ የተገኘ: {acc_summary['total_won']} ብር\n"
    
    net_profit = acc_summary['total_won'] - acc_summary['total_withdrawn']
    msg += f"\n💰 የተጣራ ትርፍ: *{net_profit} ብር*"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

# ==================== ዋናው ተግባር ====================

def main():
    """ቦቱን ማስነሳት"""
    print("🔴 ቢንጎ ቦት እየተነሳ ነው...")
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("balance", balance))
        app.add_handler(CommandHandler("deposit", deposit))
        app.add_handler(CommandHandler("withdraw", withdraw))
        app.add_handler(CommandHandler("newgame", newgame))
        app.add_handler(CommandHandler("buycards", buycards))
        app.add_handler(CommandHandler("cards", cards))
        app.add_handler(CommandHandler("call", call))
        app.add_handler(CommandHandler("leaderboard", leaderboard))
        app.add_handler(CommandHandler("history", history))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("summary", summary))
        app.add_handler(CallbackQueryHandler(join_game, pattern='join'))
        
        print("🔴 ቢንጎ ቦት ተጀምሯል! 🎲")
        print("✅ Bot is polling for updates...")
        
        app.run_polling()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
