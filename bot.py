"""
Anketa bot — savollarni ketma-ket beradi va javoblarni Telegram kanalga yuboradi.

O'RNATISH:
    pip install python-telegram-bot --upgrade

SOZLASH:
    1. Pastdagi BOT_TOKEN ni @BotFather dan olgan tokeningiz bilan almashtiring.
    2. CHANNEL_ID ni o'z kanalingiz ID/username bilan almashtiring
       (masalan: "@mening_kanalim" yoki -1001234567890).
    3. Botni kanalingizga ADMIN qilib qo'shing (xabar yuborish huquqi bilan).
    4. QUESTIONS ro'yxatiga xohlagancha savol qo'shishingiz yoki o'zgartirishingiz mumkin.

ISHGA TUSHIRISH:
    python bot.py
"""

import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ====== SOZLAMALAR (shu joyni to'ldiring) ======
BOT_TOKEN = "8063913200:AAE0YwOH68shW3_4b4Wx0DlM1t63ma0zhf0"
CHANNEL_ID = -1003950560998

# Savollarni shu yerda o'zgartiring/qo'shing. Har bir savol uchun (kalit, matn).
QUESTIONS = [
    ("full_name", "Ism va familiyangizni to'liq kiriting:"),
    ("phone", "Telefon raqamingizni kiriting:"),
    ("age", "Tug'ilgan kun,oy,yil:"),
    ("city", "Yashash manzilingiz to'liq"),
    ("comment", "Ma'lumotingiz qanday?:"),
    ("comment", "Hozirgi vaqtda o'qiysizmi? O'qish joyingiz, kursingiz, ta'lim shaklini yozing:"),
    ("comment", "Oldin ishlagan ish joylaringiz nomi, ishlagan vaqtingiz va lavozimingizni yozing.:"),
    ("comment", "Oxirgi ish joyingizdan siz haqingizda ma'lumot olsak qarshi emasmisiz? O'sha ish joyingizning telefon raqamini yozing.:"),
    ("comment", "Haydovchilik guvohnomangiz bormi?:"),
    ("comment", "Oilalimisiz? Farzandlaringiz nechta?:"),
    ("comment", "Siz bizning kompaniyada doimiy ishlamoqchimisiz?:"),
    ("comment", "Kompyuterda ishlashni bilasizmi? (Excel, Word, 1C):"),
    ("comment", "O'zingizni kompaniya taraqqiyotiga qanday hissa qo'shishingiz mumkin deb o'ylaysiz?:"),
    ("comment", "Qanday maosh sizni qoniqtiradi?:"),
    ("comment", "Eng kamida qancha maoshga ishlagan bo'lar edingiz?:"),
    ("comment", "Sudlanganmisiz?:"),
    ("comment", "Ijtimoiy tarmoqlarda faolmisiz? Username yozib qoldiring (telegram, instagram):"),
    ("recent_photo", "Iltimos so'nggi 2 oyda tushga rasmingizni yuboring. ⚠ Agar rasm yuorilmasa anketangiz qabul qilinmaydi:", "photo"),
    ("comment", "E'tiboringiz uchun katta raxmat. Tez orada siz bilan bog'lanamiz:"),
]
# ================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Har bir savolga alohida state raqami beramiz
ASKING = range(len(QUESTIONS))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Assalomu alaykum! 👋\n\nIltimos, quyidagi anketani to'ldiring.",
        reply_markup=ReplyKeyboardRemove(),
    )
    # Birinchi savolni yuboramiz
    key, question_text = QUESTIONS[0]
    await update.message.reply_text(question_text)
    return 0


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_step = context.user_data.get("step", 0)
    key, _ = QUESTIONS[current_step]
    context.user_data[key] = update.message.text

    next_step = current_step + 1
    context.user_data["step"] = next_step

    if next_step < len(QUESTIONS):
        # Keyingi savolni beramiz
        _, next_question = QUESTIONS[next_step]
        await update.message.reply_text(next_question)
        return next_step
    else:
        # Barcha savollar tugadi — natijani yig'amiz va kanalga yuboramiz
        user = update.effective_user
        lines = ["📋 <b>Yangi anketa</b>\n"]
        for key, question_text in QUESTIONS:
            lines.append(f"<b>{question_text}</b>\n{context.user_data.get(key, '-')}\n")
        lines.append(f"👤 Yuboruvchi: @{user.username or user.first_name} (id: {user.id})")
        result_text = "\n".join(lines)

        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID, text=result_text, parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Kanalga yuborishda xatolik: {e}")

        await update.message.reply_text(
            "Rahmat! Anketangiz qabul qilindi ✅", reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Anketa bekor qilindi. Qayta boshlash uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    states = {
        step: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)]
        for step in ASKING
    }

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states=states,
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
