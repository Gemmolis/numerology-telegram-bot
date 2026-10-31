import logging

from telegram import BotCommand
from telegram.constants import BotCommandScopeType
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, ASTROLOG_CHAT_ID
from db import init_db
from handlers import (
    start,
    help_command,
    moon_day,
    moon_sign,
    advice,
    consult,
    consult_question,
    button_callback,
    astrolog_answer_text,
    admin,
    admin_new,
    admin_paid,
    admin_answered,
    main_menu_router,  # <- новый обработчик
)
from states import HoraryOrder, AstrologAnswer


async def setup_commands(application: Application):
    """Настроить команды для клиентов и отдельно для астролога."""

    # 1. Сначала очищаем глобальные команды
    await application.bot.set_my_commands([])

    # 2. Команды для всех обычных пользователей (глобальные)
    user_commands = [
        BotCommand("start", "Приветствие и краткое описание бота"),
        BotCommand("help", "Справка по командам"),
        BotCommand("moon_day", "Текущий лунный день"),
        BotCommand("moon_sign", "Текущий знак Луны и прогноз"),
        BotCommand("advice", "Случайный астрологический совет"),
        BotCommand("consult", "Оформить заявку на консультацию"),
    ]
    await application.bot.set_my_commands(user_commands)

    # 3. Команды для астролога только в его чате
    if ASTROLOG_CHAT_ID:
        admin_commands = user_commands + [
            BotCommand("admin", "Последние 10 заявок"),
            BotCommand("admin_new", "Новые заявки"),
            BotCommand("admin_paid", "Оплаченные заявки"),
            BotCommand("admin_answered", "Отвеченные заявки"),
        ]
        await application.bot.set_my_commands(
            admin_commands,
            scope={"type": BotCommandScopeType.CHAT, "chat_id": ASTROLOG_CHAT_ID},
        )


def main():
    # Инициализация БД
    init_db()

    # Создаём приложение бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Пользовательские команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("moon_day", moon_day))
    application.add_handler(CommandHandler("moon_sign", moon_sign))
    application.add_handler(CommandHandler("advice", advice))

        # Обработка нажатий по клавиатуре главного меню
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            main_menu_router,
        )
    )


    # Диалог /consult
    consult_conv = ConversationHandler(
        entry_points=[CommandHandler("consult", consult)],
        states={
            HoraryOrder.waiting_question: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, consult_question)
            ],
        },
        fallbacks=[],
    )
    application.add_handler(consult_conv)

    # Диалог ответа астролога (вход в состояние задаётся из callback-кнопки)
    answer_conv = ConversationHandler(
        entry_points=[],
        states={
            AstrologAnswer.waiting_answer_text: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, astrolog_answer_text)
            ],
        },
        fallbacks=[],
    )
    application.add_handler(answer_conv)

    # Callback-кнопки (знаки зодиака + админ-кнопки по заявкам)
    application.add_handler(CallbackQueryHandler(button_callback))

    # Админ-команды (дополнительно внутри обработчиков всё равно проверяем ID)
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("admin_new", admin_new))
    application.add_handler(CommandHandler("admin_paid", admin_paid))
    application.add_handler(CommandHandler("admin_answered", admin_answered))

    # Настройка команд после инициализации бота
    application.post_init = setup_commands

    logging.info("astroMoonBot успешно запущен и слушает обновления.")
    print("astroMoonBot запущен. Нажми Ctrl+C для остановки.")

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()
