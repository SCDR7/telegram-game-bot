# bot.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Импортируем функции из SQLite версии базы данных
from db_sqlite import add_user, get_user_status, update_subscription, update_verification, mark_registered

# Настройки из config.py
from config import BOT_TOKEN, CHANNEL_ID, VERIF_CHANNEL_ID, PROMO_CODE, SUPPORT_LINK, ADMIN_ID

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запустил бота")

    # Добавляем пользователя в БД, если его нет
    add_user(user_id)

    try:
        # Проверяем подписку на основной канал
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        is_subscribed = chat_member.status in ['member', 'administrator', 'creator']
        update_subscription(user_id, is_subscribed)

        # Проверяем участие в чате верификации (постбеки)
        verif_member = await context.bot.get_chat_member(VERIF_CHANNEL_ID, user_id)
        is_in_verif = verif_member.status in ['member', 'administrator', 'creator']
        update_verification(user_id, is_in_verif)

        # Если пользователь в постбеках → считаем, что он зарегистрирован
        if is_in_verif:
            mark_registered(user_id)

    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        await update.message.reply_text("Произошла ошибка при проверке подписки.")
        return

    status = get_user_status(user_id)

    # Если подписан и состоит в постбеках → сразу открываем доступ
    if status["subscribed"] and status["verif_joined"]:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Открыть игру", web_app={"url": "https://telegram-game-bot-agfc.onrender.com"}) 
        ]])
        await update.message.reply_text("Доступ открыт!", reply_markup=keyboard)
        return

    # Если только подписка есть → просим присоединиться к постбекам
    elif status["subscribed"]:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Присоединиться к обсуждению", url=SUPPORT_LINK)
        ]])
        await update.message.reply_text("Подпишитесь на обсуждение канала.", reply_markup=keyboard)
    
    # Нет подписки → просим подписаться
    else:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Подписаться на канал", url="https://t.me/+-CNLz4Ywnx80NmYy") 
        ]])
        await update.message.reply_text("Подпишитесь на наш канал, чтобы продолжить.", reply_markup=keyboard)


# Команда /gameslot — открытие игры напрямую
async def gameslot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} вызвал команду /gameslot")

    try:
        # Проверяем, состоит ли пользователь в чате с постбеками
        verif_member = await context.bot.get_chat_member(VERIF_CHANNEL_ID, user_id)
        is_in_verif = verif_member.status in ['member', 'administrator', 'creator']

        # Если состоит → разрешаем доступ
        if is_in_verif:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Открыть игру", web_app={"url": "https://silver-hornets-sneeze.loca.lt"}) 
            ]])
            await update.message.reply_text("Доступ через /gameslot открыт!", reply_markup=keyboard)
        else:
            await update.message.reply_text("У вас нет доступа через /gameslot. Подпишитесь на канал и участвуйте в постбеках.")
    except Exception as e:
        logger.error(f"Ошибка при проверке участия в постбеках: {e}")
        await update.message.reply_text("Не удалось проверить ваш статус.")


# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()

    if text == "я зарегистрировался":
        status = get_user_status(user_id)

        if status["subscribed"] and status["verif_joined"]:
            mark_registered(user_id)
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Открыть игру", web_app={"url": "https://silver-hornets-sneeze.loca.lt"}) 
            ]])
            await update.message.reply_text("Доступ открыт!", reply_markup=keyboard)
        else:
            await update.message.reply_text("Сначала подпишитесь на канал и участвуйте в обсуждении.")
    else:
        await update.message.reply_text("Напишите 'я зарегистрировался' после регистрации.")


# Команда /check — только для админа
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    target_id = int(context.args[0]) if context.args else user_id
    status = get_user_status(target_id)

    await update.message.reply_text(
        f"Статус пользователя {target_id}:\n"
        f"Подписка: {'✅' if status['subscribed'] else '❌'}\n"
        f"Верификация: {'✅' if status['verif_joined'] else '❌'}\n"
        f"Регистрация: {'✅' if status['registered'] else '❌'}"
    )


# Запуск бота
if __name__ == '__main__':
    from db_sqlite import init_db
    init_db()  # Инициализируем SQLite базу

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gameslot", gameslot))  # <-- Новая команда
    application.add_handler(CommandHandler("check", check))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен...")
    application.run_polling()
