"""
Anketa bot — savollarni ketma-ket beradi, rasm so'raydi va javoblarni Telegram guruh/kanalga yuboradi.

O'RNATISH:
    pip install python-telegram-bot --upgrade

SOZLASH:
    1. BOT_TOKEN va CHANNEL_ID ni pastda yoki Railway'dagi Variables bo'limida bering.
    2. Botni guruh/kanalga ADMIN qilib qo'shing (xabar yuborish huquqi bilan).
    3. QUESTIONS ro'yxatiga xohlagancha savol qo'shishingiz yoki o'zgartirishingiz mumkin.
       Har bir savol: (noyob_kalit, savol_matni, turi) — turi "text" yoki "photo".

ISHGA TUSHIRISH:
    python bot.py
"""

import os
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

# ====== SOZLAMALAR ======
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8063913200:AAE0YwOH68shW3_4b4Wx0DlM1t63ma0zhf0")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1003950560998")

# Anketa yakunida ko'rsatiladigan xabar (bu savol emas, oxirgi rahmat xabari)
FINISH_MESSAGE = "E'tiboringiz uchun katta rahmat. Tez orada siz bilan bog'lanamiz."

# Savollar — har biri: (noyob_kalit, savol_matni, turi)
QUESTIONS = [
    ("full_name", "Ism va familiyangizni to'liq kiriting:", "text"),
    ("phone", "Telefon raqamingizni kiriting:", "text"),
    ("birth_date", "Tug'ilgan kun,oy,yil:", "text"),
    ("address", "Yashash manzilingiz to'liq", "text"),
    ("education", "Ma'lumotingiz qanday?:", "text"),
    ("study_status", "Hozirgi vaqtda o'qiysizmi? O'qish joyingiz, kursingiz, ta'lim shaklini yozing:", "text"),
    ("work_history", "Oldin ishlagan ish joylaringiz nomi, ishlagan vaqtingiz va lavozimingizni yozing.:", "text"),
    ("reference_contact", "Oxirgi ish joyingizdan siz haqingizda ma'lumot olsak qarshi emasmisiz? O'sha ish joyingizning telefon raqamini yozing.:", "text"),
    ("driver_license", "Haydovchilik guvohnomangiz bormi?:", "text"),
    ("family", "Oilalimisiz? Farzandlaringiz nechta?:", "text"),
    ("employment_intent", "Siz bizning kompaniyada doimiy ishlamoqchimisiz?:", "text"),
    ("computer_skills", "Kompyuterda ishlashni bilasizmi? (Excel, Word, 1C):", "text"),
    ("contribution", "O'zingizni kompaniya taraqqiyotiga qanday hissa qo'shishingiz mumkin deb o'ylaysiz?:", "text"),
    ("salary_expectation", "Qanday maosh sizni qoniqtiradi?:", "text"),
    ("min_salary", "Eng kamida qancha maoshga ishlagan bo'lar edingiz?:", "text"),
    ("criminal_record", "Sudlanganmisiz?:", "text"),
    ("social_media", "Ijtimoiy tarmoqlarda faolmisiz? Username yozib qoldiring (telegram, instagram):", "text"),
    ("recent_photo", "Iltimos so'nggi 2 oyda tushgan rasmingizni yuboring. ⚠ Agar rasm yuborilmasa anketangiz qabul qilinmaydi:", "photo"),
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
    key, question_text, _ = QUESTIONS[0]
    await update.message.reply_text(question_text)
    return 0


async def _finish_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Barcha savollar tugagach — natijalarni guruh/kanalga yuboradi."""
    user = update.effective_user
    lines = ["📋 <b>Yangi anketa</b>\n"]
    photo_file_id = None

    for key, question_text, q_type in QUESTIONS:
        if q_type == "photo":
            photo_file_id = context.user_data.get(key)
            lines.append(f"<b>{question_text}</b>\n(rasm quyida biriktirilgan)\n")
        else:
            lines.append(f"<b>{question_text}</b>\n{context.user_data.get(key, '-')}\n")

    lines.append(f"👤 Yuboruvchi: @{user.username or user.first_name} (id: {user.id})")
    result_text = "\n".join(lines)

    try:
        if photo_file_id:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=result_text, parse_mode="HTML")
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo_file_id)
        else:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=result_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Guruh/kanalga yuborishda xatolik: {e}")

    await update.effective_message.reply_text(FINISH_MESSAGE, reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


async def handle_text_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_step = context.user_data.get("step", 0)
    key, _, _ = QUESTIONS[current_step]
    context.user_data[key] = update.message.text

    next_step = current_step + 1
    context.user_data["step"] = next_step

    if next_step < len(QUESTIONS):
        _, next_question, _ = QUESTIONS[next_step]
        await update.message.reply_text(next_question)
        return next_step
    return await _finish_survey(update, context)


async def handle_photo_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_step = context.user_data.get("step", 0)
    key, _, _ = QUESTIONS[current_step]

    if not update.message.photo:
        await update.message.reply_text("Iltimos, rasm (fotosurat) shaklida yuboring.")
        return current_step

    context.user_data[key] = update.message.photo[-1].file_id

    next_step = current_step + 1
    context.user_data["step"] = next_step

    if next_step < len(QUESTIONS):
        _, next_question, _ = QUESTIONS[next_step]
        await update.message.reply_text(next_question)
        return next_step
    return await _finish_survey(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Anketa bekor qilindi. Qayta boshlash uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    states = {}
    for step, (_, _, q_type) in enumerate(QUESTIONS):
        if q_type == "photo":
            states[step] = [MessageHandler(filters.PHOTO, handle_photo_answer)]
        else:
            states[step] = [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_answer)]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states=states,
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
