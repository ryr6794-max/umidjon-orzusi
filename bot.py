[7/9/2026 09:03 AM] .: import logging
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)

TOKEN = os.environ.get("BOT_TOKEN")

NAME, AGE, CITY, BIO, GENDER, LOOKING_FOR = range(6)

users = {}
likes = {}
matches = {}
passes = {}


def get_profile_text(profile):
    gender_emoji = "Ayol" if profile.get("gender") == "ayol" else "Erkak"
    return (
        "*" + profile['name'] + "*, " + str(profile['age']) + " yosh\n"
        "Shahar: " + profile['city'] + "\n\n"
        "Bio: " + profile['bio']
    )


def get_next_user(current_id):
    seen = set(likes.get(current_id, []) + passes.get(current_id, []) + [current_id])
    current_profile = users.get(current_id, {})
    looking_for = current_profile.get("looking_for", "hammasi")

    candidates = []
    for uid, profile in users.items():
        if uid in seen:
            continue
        if looking_for != "hammasi":
            if profile.get("gender") != looking_for:
                continue
        candidates.append((uid, profile))

    if not candidates:
        return None

    uid, profile = random.choice(candidates)
    profile["_id"] = uid
    return profile


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in users:
        await update.message.reply_text(
            "Xush kelibsiz!\n"
            "/topish - yangi odamlarni ko'rish\n"
            "/moslashuvlar - matchlaringiz\n"
            "/profil - profilingiz"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "TanishBot'ga xush kelibsiz!\n\n"
        "Ismingizni kiriting:",
        parse_mode="Markdown"
    )
    return NAME


async def get_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Yoshingiz nechida?")
    return AGE


async def get_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or not (16 <= int(text) <= 60):
        await update.message.reply_text("Iltimos, togri yosh kiriting (16-60):")
        return AGE
    ctx.user_data["age"] = int(text)
    await update.message.reply_text("Qaysi shaharda yashaysiz?")
    return CITY


async def get_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["city"] = update.message.text.strip()
    await update.message.reply_text("Oz haqingizda qisqacha yozing:")
    return BIO


async def get_bio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["bio"] = update.message.text.strip()
    keyboard = [[
        InlineKeyboardButton("Erkak", callback_data="gender_erkak"),
        InlineKeyboardButton("Ayol", callback_data="gender_ayol"),
    ]]
    await update.message.reply_text(
        "Jinsingiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GENDER


async def get_gender(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["gender"] = query.data.split("_")[1]

    keyboard = [[
        InlineKeyboardButton("Erkak", callback_data="looking_erkak"),
        InlineKeyboardButton("Ayol", callback_data="looking_ayol"),
        InlineKeyboardButton("Hammasi", callback_data="looking_hammasi"),
    ]]
    await query.message.reply_text(
        "Kimni qidiryapsiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LOOKING_FOR


async def get_looking_for(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["looking_for"] = query.data.split("_")[1]

    user_id = query.from_user.id
    users[user_id] = ctx.user_data.copy()
    likes[user_id] = []
    passes[user_id] = []
    matches[user_id] = []
[7/9/2026 09:03 AM] .: await query.message.reply_text(
        "Profil yaratildi!\n\n" + get_profile_text(users[user_id]) + "\n\n"
        "/topish - odamlarni korish boshlang!",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def topish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        await update.message.reply_text("Avval royxatdan oting: /start")
        return

    candidate = get_next_user(user_id)
    if not candidate:
        await update.message.reply_text(
            "Hozircha korsatadigan odam qolmadi.\n"
            "/reset bilan tozalab qayta boshlang."
        )
        return

    cid = candidate["_id"]
    keyboard = [[
        InlineKeyboardButton("Pass", callback_data="pass_" + str(cid)),
        InlineKeyboardButton("Like", callback_data="like_" + str(cid)),
    ], [
        InlineKeyboardButton("Super Like", callback_data="superlike_" + str(cid)),
    ]]
    await update.message.reply_text(
        get_profile_text(candidate),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    action, target_id_str = query.data.rsplit("_", 1)
    target_id = int(target_id_str)

    if action == "pass":
        passes.setdefault(user_id, []).append(target_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await show_next(query, user_id, ctx)

    elif action in ("like", "superlike"):
        likes.setdefault(user_id, []).append(target_id)

        if user_id in likes.get(target_id, []):
            matches.setdefault(user_id, []).append(target_id)
            matches.setdefault(target_id, []).append(user_id)

            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                "Moslik topildi!\n\n"
                + users[target_id]['name'] + " ham sizni yoqtirgan edi!\n"
                "/moslashuvlar - barchani korish"
            )
            try:
                await ctx.bot.send_message(
                    chat_id=target_id,
                    text="Moslik! " + users[user_id]['name'] + " bilan moslashdingiz!\n/moslashuvlar"
                )
            except Exception:
                pass
        else:
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("Yoqtirdingiz!")

            if action == "superlike":
                try:
                    await ctx.bot.send_message(
                        chat_id=target_id,
                        text="Kimdir sizni Super Like qildi! /topish"
                    )
                except Exception:
                    pass

        await show_next(query, user_id, ctx)


async def show_next(query, user_id, ctx):
    candidate = get_next_user(user_id)
    if not candidate:
        await query.message.reply_text("Korsatadigan odam qolmadi. Keyinroq keling!")
        return

    cid = candidate["_id"]
    keyboard = [[
        InlineKeyboardButton("Pass", callback_data="pass_" + str(cid)),
        InlineKeyboardButton("Like", callback_data="like_" + str(cid)),
    ], [
        InlineKeyboardButton("Super Like", callback_data="superlike_" + str(cid)),
    ]]
    await query.message.reply_text(
        get_profile_text(candidate),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def moslashuvlar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_matches = matches.get(user_id, [])

    if not user_matches:
        await update.message.reply_text("Hali moslashuvlar yoq.\n/topish - odamlarni koring!")
        return

    text = "Moslashuvlaringiz:\n\n"
    for mid in user_matches:
        if mid in users:
            p = users[mid]
            text += "- " + p['name'] + ", " + str(p['age']) + " - " + p['city'] + "\n"
[7/9/2026 09:03 AM] .: await update.message.reply_text(text)


async def profil(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        await update.message.reply_text("Avval /start bilan royxatdan oting.")
        return

    profile = users[user_id]
    stats = (
        "Like berilgan: " + str(len(likes.get(user_id, []))) + "\n"
        "Moslashuvlar: " + str(len(matches.get(user_id, []))) + "\n"
    )
    await update.message.reply_text(
        get_profile_text(profile) + "\n\n" + stats,
        parse_mode="Markdown"
    )


async def reset_passes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    passes[user_id] = []
    await update.message.reply_text("Ochirilganlar tozalandi! /topish")


def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            GENDER: [CallbackQueryHandler(get_gender, pattern="^gender_")],
            LOOKING_FOR: [CallbackQueryHandler(get_looking_for, pattern="^looking_")],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("topish", topish))
    app.add_handler(CommandHandler("moslashuvlar", moslashuvlar))
    app.add_handler(CommandHandler("profil", profil))
    app.add_handler(CommandHandler("reset", reset_passes))
    app.add_handler(CallbackQueryHandler(handle_action, pattern="^(like|pass|superlike)_"))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if name == "main":
    main()
