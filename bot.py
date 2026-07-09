import logging
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

# Conversation states
NAME, AGE, CITY, BIO, GENDER, LOOKING_FOR = range(6)

# In-memory database (Render uchun yetarli, keyinchalik PostgreSQL qo'shish mumkin)
users = {}       # {user_id: {...profile}}
likes = {}       # {user_id: [liked_user_ids]}
matches = {}     # {user_id: [matched_user_ids]}
passes = {}      # {user_id: [passed_user_ids]}


def get_profile_text(profile: dict) -> str:
    gender_emoji = "👩" if profile.get("gender") == "ayol" else "👨"
    return (
        f"{gender_emoji} *{profile['name']}*, {profile['age']} yosh\n"
        f"📍 {profile['city']}\n\n"
        f"💬 _{profile['bio']}_"
    )


def get_next_user(current_id: int) -> dict | None:
    """Tasodifiy foydalanuvchi tanlash (ko'rilmaganlardan)"""
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
            "👋 Xush kelibsiz! /topish — yangi odamlarni ko'rish\n"
            "/moslashuvlar — matchlaringiz\n"
            "/profil — profilingiz"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "💕 *TanishBot*'ga xush kelibsiz!\n\n"
        "Ro'yxatdan o'tish uchun bir necha savol beramiz.\n\n"
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
        await update.message.reply_text("❌ Iltimos, to'g'ri yosh kiriting (16-60):")
        return AGE
    ctx.user_data["age"] = int(text)
    await update.message.reply_text("Qaysi shaharda yashaysiz?")
    return CITY


async def get_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["city"] = update.message.text.strip()
    await update.message.reply_text("O'zingiz haqingizda qisqacha yozing (bio):")
    return BIO


async def get_bio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["bio"] = update.message.text.strip()
    keyboard = [[
        InlineKeyboardButton("👨 Erkak", callback_data="gender_erkak"),
        InlineKeyboardButton("👩 Ayol", callback_data="gender_ayol"),
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

    keyboard = [[]]
        InlineKeyboardButton("👨 Erkak", callback_data="looking_erkak"),
