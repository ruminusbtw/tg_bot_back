import os
import django
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from asgiref.sync import sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegrambot.settings')
django.setup()

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📋 Список товаров", "➕ Добавить товар"],
        ["ℹ️ Помощь"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот для управления базой данных.\nВыберите действие:",
        reply_markup=MAIN_MENU_KEYBOARD
    )

@sync_to_async
def get_product_list():
    from tg_bot.models import Product
    products = Product.objects.all()
    if not products:
        return "Нет товаров в базе данных."
    return "\n".join([f"{product.name} - {product.price}" for product in products])

async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    product_list = await get_product_list()  
    await update.message.reply_text(product_list)

async def add_item_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Введите данные товара в формате: название, цена\nНапример: Телефон, 15000"
    )
    context.user_data['adding_item'] = True

async def add_item_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('adding_item'):
        user_input = update.message.text.strip()

        if ',' not in user_input:
            await update.message.reply_text(
                "Ошибка: введите данные в формате: название, цена.\n"
                "Пример: Телефон, 15000"
            )
            return

        try:
            name, price = map(str.strip, user_input.split(",", 1))
            price = float(price)  
            
            from tg_bot.models import Product

            product = Product.objects.create(name=name, price=price)
            await update.message.reply_text(f"Товар '{name}' добавлен по цене {price}!")

            product_list = await get_product_list()
            await update.message.reply_text(f"Обновленный список товаров:\n{product_list}")
        except ValueError:
            await update.message.reply_text(
                "Ошибка: цена должна быть числом. Попробуйте снова."
            )
        finally:
            context.user_data['adding_item'] = False
    else:
        await update.message.reply_text("Неизвестная команда. Используйте меню.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я помогу вам управлять базой данных товаров.\n"
        "Команды:\n"
        "📋 Список товаров - показывает все товары в базе.\n"
        "➕ Добавить товар - добавляет новый товар.\n"
        "ℹ️ Помощь - показывает это сообщение."
    )

app = ApplicationBuilder().token("7836141518:AAF2yIP7K7jCf-dMn_HjrcRyfCwDCSEpe2w").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Text("📋 Список товаров"), list_items))
app.add_handler(MessageHandler(filters.Text("➕ Добавить товар"), add_item_prompt))
app.add_handler(MessageHandler(filters.Text("ℹ️ Помощь"), help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_process))

if __name__ == "__main__":
    app.run_polling()
