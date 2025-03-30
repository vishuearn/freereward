from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import logging
import time

from telegram.ext import MessageHandler, Filters


import json
import os

DATA_FILE = "data.json"


# Load data from JSON file
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


# Save data to JSON file
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_referral(referrer_id, new_user_id):
    data = load_data()

    # Initialize referrer data if not exists
    if str(referrer_id) not in data:
        data[str(referrer_id)] = {
            "balance": 1,
            "referrals": []
        }  # Referrer already gets ₹1 signup

    # Only reward if not referred already
    if str(new_user_id) not in data[str(referrer_id)]["referrals"]:
        data[str(referrer_id)]["referrals"].append(str(new_user_id))
        data[str(referrer_id)]["balance"] += 1  # Referral reward ₹1

    # Give signup bonus to the new user
    if str(new_user_id) not in data:
        data[str(new_user_id)] = {
            "balance": 1,
            "referrals": []
        }  # Signup bonus ₹1

    save_data(data)


# ✅ Replace with your actual bot token
TOKEN = "8019280976:AAEZ_79jNbWx-yKUhE-PeeGi3IYvEk44nfA"

# ✅ Replace with your actual channel usernames (WITHOUT @)
CHANNELS = [
    "whatsappagentloot2", "visalearnings", "without_investment_earning_mone"
]

# ✅ Set up logging to debug issues
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# ✅ Function to check if the user is in all required channels
def is_user_in_all_channels(user_id, context):
    bot = context.bot
    for channel in CHANNELS:
        try:
            chat_member = bot.get_chat_member(f"@{channel}", user_id)
            if chat_member.status not in [
                    "member", "administrator", "creator"
            ]:
                return False  # ❌ User is NOT a member
        except Exception as e:
            logger.error(f"Error checking {channel}: {e}")
            return False
    return True  # ✅ User is in all channels


# ✅ Start Command - Check if user has joined channels
def start(update: Update, context: CallbackContext):
    user_id = str(update.message.chat.id)
    args = context.args

    data = load_data()

    # ✅ Naya user hai to ₹1 signup bonus dega
    if user_id not in data:
        data[user_id] = {"balance": 1, "referrals": []}
        save_data(data)

    # ✅ Agar user referral link se aaya hai, to referrer ko reward milega
    if args:
        referrer_id = args[0]
        if referrer_id.isdigit() and referrer_id != user_id:
            add_referral(referrer_id, user_id)

    # ✅ Pehle check karega ki user ne channels join kiye ya nahi
    if not is_user_in_all_channels(user_id, context):
        send_join_message(update)  # Agar nahi join kiya to join message show karega
    else:
        show_main_menu(update, context)  # Agar join kar liya hai to sidha dashboard dikhega



def check_balance(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)  # ✅ Works for both commands & buttons
    data = load_data()

    if user_id in data:
        balance = data[user_id]["balance"]
        referrals = len(data[user_id]["referrals"])
    else:
        balance = 0
        referrals = 0

    update.effective_message.reply_text(
        f"💰 Your Balance: ₹{balance}\n"
        f"👥 Total Referrals: {referrals}\n"
        f"💸 Minimum Withdrawal: ₹5",
        parse_mode="Markdown")




def show_referral_details(update: Update, context: CallbackContext):
    user_id = str(update.message.chat.id)

    # 🛑 Check if the user is admin
    if user_id != "5018478747":  # ❗️Apna Admin ID yahaan daalein
        update.message.reply_text(
            "❌ You are not authorized to view this data!")
        return

    data = load_data()
    referral_data = "\n".join([
        f"User {user}: {len(info['referrals'])} referrals"
        for user, info in data.items()
    ])

    if not referral_data:
        referral_data = "No referral data available."

    update.message.reply_text(f"📊 *Referral Stats:*\n\n{referral_data}",
                              parse_mode="Markdown")


# ✅ Function to send join message with buttons
def send_join_message(update: Update):
    keyboard = [[
        InlineKeyboardButton(f"Join {channel}", url=f"https://t.me/{channel}")
    ] for channel in CHANNELS]
    keyboard.append(
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "❌ You must join all channels to continue. After joining, click **'I Joined'**:",
        reply_markup=reply_markup)


# ✅ Callback when user clicks "I Joined"
def check_join(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    logger.info(f"✅ User {user_id} clicked 'I Joined' button")

    if is_user_in_all_channels(user_id, context):
        query.message.delete()  # ✅ Remove the join message
        show_main_menu(update, context)
    else:
        query.answer("❌ You have not joined all channels. Please join first!", show_alert=True)


def handle_menu_click(update: Update, context: CallbackContext):
    message = update.message.text.strip().lower()

    # ✅ अगर बॉट UPI ID या withdrawal amount का इंतजार कर रहा है, तो कोई invalid message न भेजे
    if context.user_data.get("awaiting_upi") or context.user_data.get("awaiting_amount"):
        return

    if message in ["menu", "/menu", "start", "/start"]:
        show_main_menu(update, context)  # 🔥 मुख्य मेनू दिखाएं
    else:
        update.message.reply_text("❌ Invalid option! Type 'Menu' to see options.")







# ✅ Show the Main Menu
from telegram import ReplyKeyboardMarkup

def show_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")
        ],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text("✅ Welcome! Choose an option:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        query.answer()
        query.message.edit_text("✅ Welcome! Choose an option:", reply_markup=reply_markup)





def handle_button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return

    query.answer()

    if query.data == "balance":
        check_balance(update, context)  # ✅ Fix applied
    elif query.data == "refer":
        bot_username = context.bot.username
        referral_link = f"https://t.me/{bot_username}?start={query.from_user.id}"
        query.message.reply_text(
            f"📢 *Share your referral link:*\n\n🔗 {referral_link}\n👥 Earn ₹1 per invite!",
            parse_mode="Markdown")
    elif query.data == "withdraw":
        withdraw_request(update, context)






def withdraw_request(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()

    if user_id in data and data[user_id]["balance"] >= 5:
        query.answer()
        query.message.reply_text("💸 Please send your *UPI ID*:", parse_mode="Markdown")
        context.user_data["awaiting_upi"] = True  # Waiting for UPI ID
    else:
        query.answer()
        query.message.reply_text("❌ *You need at least ₹5 to withdraw.*", parse_mode="Markdown")




from telegram import BotCommand

def set_bot_commands(updater):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("menu", "Show main menu"),
        BotCommand("balance", "Check your balance"),
        BotCommand("referrals", "Show referral stats (Admin only)"),
        BotCommand("withdraw", "Request a withdrawal"),
        BotCommand("help", "Show all commands")
    ]
    updater.bot.set_my_commands(commands)



def handle_message(update: Update, context: CallbackContext):
    user_id = str(update.message.chat.id)
    message = update.message.text.strip()
    data = load_data()

    # ✅ Step 1: अगर UPI ID की मांग की गई है, तो उसे स्टोर करें
    if context.user_data.get("awaiting_upi"):
        context.user_data["upi_id"] = message  # 🔥 UPI ID स्टोर करें
        context.user_data["awaiting_upi"] = False  # ✅ अब UPI का इंतजार खत्म
        context.user_data["awaiting_amount"] = True  # ✅ अब amount का इंतजार होगा  

        update.message.reply_text(
            "✅ *UPI ID saved!* Now enter the amount you want to withdraw (Minimum ₹5):",
            parse_mode="Markdown"
        )
        return  # ✅ इस लाइन को जोड़ना ज़रूरी है ताकि आगे का कोड ना चले

    # ✅ Step 2: अगर withdrawal amount की मांग की गई है
    if context.user_data.get("awaiting_amount"):
        if not message.isdigit():
            update.message.reply_text("❌ Please enter a valid amount.")
            return

        amount = int(message)

        if amount < 5:
            update.message.reply_text("❌ Minimum withdrawal is ₹5.")
            return

        if user_id in data and data[user_id]["balance"] >= amount:
            data[user_id]["balance"] -= amount  # 🔥 बैलेंस घटाएं
            save_data(data)

            upi_id = context.user_data.get("upi_id")  # 🔥 UPI ID लोड करें

            update.message.reply_text(
                f"✅ *Withdrawal request submitted!*\n\n"
                f"📌 *Details:*\n"
                f"💰 Amount: ₹{amount}\n"
                f"💳 UPI ID: `{upi_id}`\n"
                "⏳ Please wait while the admin processes your request.\n"
                "💡 *You will receive your payment within 24 hours!*",
                parse_mode="Markdown"
            )

            # ✅ Admin को notification भेजें
            ADMIN_ID = 5018478747  # 🔥 अपने Admin का Telegram ID डालें
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📩 *New Withdrawal Request!*\n"
                    f"👤 *User ID:* `{user_id}`\n"
                    f"💰 *Amount:* ₹{amount}\n"
                    f"💳 *UPI ID:* `{upi_id}`\n"
                    "✅ *Please verify and process the payment!*"
                ),
                parse_mode="Markdown"
            )

        else:
            update.message.reply_text("❌ *You don't have enough balance to withdraw!*", parse_mode="Markdown")

        context.user_data["awaiting_amount"] = False  # ✅ Reset state

    else:
        update.message.reply_text("❌ Invalid option! Type 'Menu' to see options.")






# ✅ Set up the bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # ✅ Button Click Handlers
    dispatcher.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    dispatcher.add_handler(CallbackQueryHandler(handle_button_click))  # Inline buttons

    # ✅ Command Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("balance", check_balance))
    dispatcher.add_handler(CommandHandler("referrals", show_referral_details))
    dispatcher.add_handler(CommandHandler("menu", show_main_menu))  # ✅ /menu command
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # ✅ Text Message Handler (Menu Command)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_menu_click))
    set_bot_commands(updater)

    # Start the bot
    updater.start_polling()
    updater.idle()





if __name__ == "__main__":
    main()
