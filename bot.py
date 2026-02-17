import os
import re
import logging
from dotenv import load_dotenv

load_dotenv()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_TEXT, WAITING_CARD, WAITING_USERNAME, WAITING_ACCOUNT_TYPE = range(4)


def parse_transaction(text: str) -> dict:
    """Parse raw transaction text and extract all fields."""
    data = {}

    # Application number
    m = re.search(r"Заявка\s*№[:\s]*(\S+)", text)
    if m:
        data["order_id"] = m.group(1)

    # Exchange rate
    m = re.search(r"Курс[:\s]*(.*)", text)
    if m:
        data["rate"] = m.group(1).strip()

    # Date
    m = re.search(r"Дата создания[:\s]*(.*)", text)
    if m:
        data["date"] = m.group(1).strip()

    # Direction
    m = re.search(r"Направление[:\s]*(.*)", text)
    if m:
        data["direction"] = m.group(1).strip()

    # Service transfer - payment system
    service_block = re.search(
        r"Переводит сервис[:\s]*\n(.*?)(?:-{3,}|Информация|$)",
        text,
        re.DOTALL,
    )
    if service_block:
        block = service_block.group(1)

        m = re.search(r"ПС[:\s]*(.*)", block)
        if m:
            data["ps"] = m.group(1).strip()

        m = re.search(r"Сумма[:\s]*(.*)", block)
        if m:
            data["amount"] = m.group(1).strip()

        m = re.search(r"На счет[:\s]*(.*)", block)
        if m:
            data["account"] = m.group(1).strip()

    # Client sends - payment system and amount
    client_block = re.search(
        r"Отдает клиент[:\s]*\n(.*?)(?:Переводит|$)",
        text,
        re.DOTALL,
    )
    if client_block:
        block = client_block.group(1)

        m = re.search(r"ПС[:\s]*(.*)", block)
        if m:
            data["client_ps"] = m.group(1).strip()

        m = re.search(r"Сумма[:\s]*(.*)", block)
        if m:
            data["client_amount"] = m.group(1).strip()

    # User info
    m = re.search(r"E-mail[:\s]*([\S]+)", text)
    if m:
        data["email"] = m.group(1).strip()

    m = re.search(r"Имя[:\s]*(.*)", text)
    if m:
        data["name"] = m.group(1).strip()

    m = re.search(r"— ID[:\s]*(.*)", text)
    if m:
        data["user_id"] = m.group(1).strip()

    return data


def format_output(data: dict) -> str:
    """Format parsed data into a beautiful output message."""
    lines = []

    # Header with order info
    if data.get("order_id"):
        lines.append(f"📋 Заявка №: {data['order_id']}")
    if data.get("rate"):
        lines.append(f"💱 Курс: {data['rate']}")
    if data.get("date"):
        lines.append(f"📅 {data['date']}")

    lines.append("")

    # Service transfer block
    lines.append("Переводит сервис:")
    if data.get("ps"):
        lines.append(f"  — ПС: {data['ps']}")
    if data.get("amount"):
        lines.append(f"  — Сумма: {data['amount']}")

    # Account with type
    account_type = data.get("account_type", "")
    if data.get("account"):
        if account_type:
            lines.append(f"  {account_type}  {data['account']}")
        else:
            lines.append(f"  — На счет: {data['account']}")

    lines.append("")

    # Email
    if data.get("email"):
        lines.append(f"— E-mail: {data['email']}")

    lines.append("")

    # Name and card
    if data.get("name"):
        lines.append(f"{data['name']}:")
    if data.get("card"):
        lines.append(data["card"])

    # Telegram username
    if data.get("username"):
        lines.append(f"TG: {data['username']}")

    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "Привет! Я бот для форматирования заявок.\n\n"
        "Отправь мне текст заявки, и я отформатирую его красиво.\n\n"
        "Просто вставь текст заявки в чат."
    )
    return WAITING_TEXT


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and parse the transaction text."""
    raw_text = update.message.text
    data = parse_transaction(raw_text)

    if not data.get("ps") and not data.get("amount"):
        await update.message.reply_text(
            "Не удалось распознать заявку. Пожалуйста, отправь полный текст заявки."
        )
        return WAITING_TEXT

    context.user_data["parsed"] = data

    await update.message.reply_text(
        "Заявка получена!\n\n"
        "Введи номер карты (например: 2202208436545371):\n"
        "Или отправь «-» чтобы пропустить."
    )
    return WAITING_CARD


async def receive_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive card number."""
    text = update.message.text.strip()
    if text != "-":
        # Remove spaces from card number
        card = text.replace(" ", "")
        context.user_data["parsed"]["card"] = card

    await update.message.reply_text(
        "Введи Telegram username (например: @username):\n"
        "Или отправь «-» чтобы пропустить."
    )
    return WAITING_USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive telegram username."""
    text = update.message.text.strip()
    if text != "-":
        username = text if text.startswith("@") else f"@{text}"
        context.user_data["parsed"]["username"] = username

    # Ask for account type
    keyboard = [
        [
            InlineKeyboardButton("СБП", callback_data="account_type_СБП"),
            InlineKeyboardButton("Карта", callback_data="account_type_Карта"),
        ],
        [
            InlineKeyboardButton("Счёт", callback_data="account_type_Счёт"),
            InlineKeyboardButton("Пропустить", callback_data="account_type_"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выбери тип счёта:", reply_markup=reply_markup
    )
    return WAITING_ACCOUNT_TYPE


async def receive_account_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive account type from inline button."""
    query = update.callback_query
    await query.answer()

    account_type = query.data.replace("account_type_", "")
    if account_type:
        context.user_data["parsed"]["account_type"] = account_type

    data = context.user_data["parsed"]
    result = format_output(data)

    await query.edit_message_text("Готово! Вот отформатированная заявка:")
    await query.message.reply_text(result)

    # Also send a copyable version in monospace
    await query.message.reply_text(f"```\n{result}\n```", parse_mode="Markdown")

    # Clear user data
    context.user_data.clear()

    await query.message.reply_text("Отправь новую заявку для форматирования.")
    return WAITING_TEXT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current conversation."""
    context.user_data.clear()
    await update.message.reply_text("Отменено. Отправь новую заявку.")
    return WAITING_TEXT


def main():
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text),
        ],
        states={
            WAITING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text),
            ],
            WAITING_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_card),
            ],
            WAITING_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username),
            ],
            WAITING_ACCOUNT_TYPE: [
                CallbackQueryHandler(receive_account_type, pattern=r"^account_type_"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
    )

    app.add_handler(conv_handler)

    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
