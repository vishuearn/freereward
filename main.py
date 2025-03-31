from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, 
                          MessageHandler, filters, CallbackContext)
import logging
import json
import os

DATA_FILE = "data.json"
ADMIN_ID = "5018478747"  # ✅ अपना Admin ID डालें

# ✅ Load and Save JSON Data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ✅ Bot Token
TOKEN = "8019280976:AAEZ_79jNbWx-yKUhE-PeeGi3IYvEk44nfA"

# ✅ Telegram Channels
CHANNELS = ["whatsappagentloot2", "visalearnings", "without_investment_earning_mone"]

# ✅ Set Up Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Check if User is in All Channels
async def is_user_in_all_channels(user_id, application):
    for channel in CHANNELS:
        try:
            chat_member = await application.bot.get_chat_member(f"@{channel}", user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logger.error(f"Error checking {channel}: {e}")
            return False
    return True

# ✅ Start Command
async def start(update: Update, context: CallbackContext):
    user_id = str(update.message.chat.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"balance": 1, "referrals": []}
        save_data(data)

    if not await is_user_in_all_channels(user_id, context.application):
        await send_join_message(update)
    else:
        await show_main_menu(update, context)

# ✅ Send Join Message with Buttons
async def send_join_message(update: Update):
    keyboard = [[InlineKeyboardButton(f"Join {channel}", url=f"https://t.me/{channel}")] for channel in CHANNELS]
    keyboard.append([InlineKeyboardButton("✅ I Joined", callback_data="check_join")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "❌ You must join all channels to continue. Click 'I Joined' after joining:",
        reply_markup=reply_markup
    )

# ✅ Check If User Joined the Channels
async def check_join(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if await is_user_in_all_channels(user_id, context.application):
        await query.message.delete()
        await show_main_menu(query, context)
    else:
        await query.answer("❌ You have not joined all channels. Please join first!", show_alert=True)
      
# ✅ Show Main Menu
# ✅ Show Main Menu (Fix for callback issue)
async def show_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:  # ✅ Handle normal messages
        await update.message.reply_text("✅ Welcome! Choose an option:", reply_markup=reply_markup)
    elif update.callback_query:  # ✅ Handle callback queries
        query = update.callback_query
        await query.answer()
        await query.message.edit_text("✅ Welcome! Choose an option:", reply_markup=reply_markup)


# ✅ Handle Button Clicks
async def handle_button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "balance":
        await check_balance(update, context)
    elif query.data == "refer":
        bot_username = context.application.bot.username
        referral_link = f"https://t.me/{bot_username}?start={query.from_user.id}"
        await query.message.reply_text(
            f"📢 *Share your referral link:*\n\n🔗 {referral_link}\n👥 Earn ₹1 per invite!",
            parse_mode="Markdown"
        )
    elif query.data == "withdraw":
        await withdraw_request(update, context)

# ✅ Check Balance
async def check_balance(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)
    data = load_data()

    balance = data.get(user_id, {}).get("balance", 0)
    referrals = len(data.get(user_id, {}).get("referrals", []))

    await update.effective_message.reply_text(
        f"💰 Your Balance: ₹{balance}\n"
        f"👥 Total Referrals: {referrals}\n"
        f"💸 Minimum Withdrawal: ₹5",
        parse_mode="Markdown"
    )

# ✅ Handle Withdraw Request
async def withdraw_request(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()

    if data.get(user_id, {}).get("balance", 0) >= 5:
        await query.answer()
        await query.message.reply_text("💸 Please send your *UPI ID*:", parse_mode="Markdown")
        context.user_data["awaiting_upi"] = True
    else:
        await query.answer()
        await query.message.reply_text("❌ *You need at least ₹5 to withdraw.*", parse_mode="Markdown")

# ✅ Handle Text Messages
async def handle_message(update: Update, context: CallbackContext):
    user_id = str(update.message.chat.id)
    message = update.message.text.strip()
    data = load_data()

    if context.user_data.get("awaiting_upi"):
        context.user_data["upi_id"] = message
        context.user_data["awaiting_upi"] = False
        context.user_data["awaiting_amount"] = True
        await update.message.reply_text(
            "✅ *UPI ID saved!* Now enter the amount you want to withdraw (Minimum ₹5):",
            parse_mode="Markdown"
        )
        return

    if context.user_data.get("awaiting_amount"):
        if not message.isdigit():
            await update.message.reply_text("❌ Please enter a valid amount.")
            return

        amount = int(message)

        if amount < 5:
            await update.message.reply_text("❌ Minimum withdrawal is ₹5.")
            return

        if data.get(user_id, {}).get("balance", 0) >= amount:
            data[user_id]["balance"] -= amount
            save_data(data)

            upi_id = context.user_data.get("upi_id")

            # ✅ Send Message to Admin
            admin_msg = (
                f"🆕 *New Withdrawal Request!*\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"💰 Amount: ₹{amount}\n"
                f"💳 UPI ID: `{upi_id}`"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")

            await update.message.reply_text(
                f"✅ *Withdrawal request submitted!*\n\n"
                f"📌 *Details:*\n"
                f"💰 Amount: ₹{amount}\n"
                f"💳 UPI ID: `{upi_id}`\n"
                "⏳ Please wait while the admin processes your request.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ *You don't have enough balance to withdraw!*")

        context.user_data["awaiting_amount"] = False

# ✅ Show Referral Stats (Admin Only)
async def show_referral_details(update: Update, context: CallbackContext):
    if str(update.message.chat.id) != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to view this data!")
        return

    data = load_data()
    referral_data = "\n".join([f"User {user}: {len(info['referrals'])} referrals" for user, info in data.items()])

    await update.message.reply_text(f"📊 *Referral Stats:*\n\n{referral_data}", parse_mode="Markdown")

# ✅ Main Function
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("referrals", show_referral_details))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_button_click))
    app.run_polling()
    # ✅ Register Callback Query Handler
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
if __name__ == "__main__":
    main()
