import logging
import asyncio
import sys
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

from src import OPENAI_API_KEY, ASSISTANT_ID, TELEGRAM_TOKEN

# --- Инициализация клиентов ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Логирование ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
user_threads = {}


# --- Приветственное сообщение ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник.\n"
        "Отправь любое сообщение, и я передам его ассистенту OpenAI."
    )
    
    
# --- Основная логика ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id

    status_msg = await update.message.reply_text("Обрабатываю запрос...")

    try:
        # Создаем или получаем thread для пользователя
        if user_id in user_threads:
            thread_id = user_threads[user_id]
        else:
            thread = client.beta.threads.create()
            thread_id = thread.id
            user_threads[user_id] = thread_id  

        # Добавляем сообщение пользователя в thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Запускаем ассистента
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Ожидаем завершения
        while run.status in ("queued", "in_progress"):
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

        # Получаем ответы ассистента
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        response_texts = [
            msg.content[0].text.value
            for msg in reversed(messages.data)
            if msg.role == "assistant"
        ]

        response = "\n".join(response_texts) if response_texts else "Нет ответа от ассистента."
        await status_msg.edit_text(response)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await status_msg.edit_text("Ошибка при обработке запроса. Попробуйте позже.")


# --- Запуск бота ---
def main():
    # Создаем приложение
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))  
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  

    print("✅ Бот запущен!")
    
    # Запускаем бота (синхронно)
    app.run_polling()


if __name__ == "__main__":
    # Для Windows: устанавливаем политику event loop если нужно
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Просто запускаем main() без asyncio.run()
    main()