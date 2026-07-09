await update.message.reply_text(text)


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
