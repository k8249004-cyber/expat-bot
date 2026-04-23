#!/usr/bin/env python3

import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = "8742721488:AAGZfB9CX7JGiW_RhCmPSUtEh6f_TS2Vc2M"
ADMIN_IDS = [7119717032]
DATA_FILE = "data.json"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

ADD_TITLE, ADD_CATEGORY, ADD_CITY, ADD_CONTENT = range(4)

CATEGORIES = {
    "housing":   ("🏠", "Жильё и аренда"),
    "schools":   ("🎓", "Школы и садики"),
    "food":      ("🍽️", "Еда и кафе"),
    "cooking":   ("👩‍🍳", "Рецепты"),
    "sights":    ("🕌", "Достопримечательности"),
    "docs":      ("📋", "Документы и визы"),
    "transport": ("🚗", "Транспорт"),
    "health":    ("🏥", "Медицина"),
    "shopping":  ("🛍️", "Шопинг"),
    "tips":      ("💡", "Лайфхаки"),
}

CITIES = {
    "jeddah": "📍 Джидда",
    "riyadh": "📍 Эр-Рияд",
    "both":   "📍 Джидда и Эр-Рияд",
    "other":  "📍 Другой город",
}

INITIAL_DATA = {
    "articles": [
        {"id": 1, "category": "housing", "city": "jeddah", "title": "Как найти квартиру в Джидде", "content": "🏘 Популярные районы:\n• Al Hamra — престижный\n• Al Rawdah — центральный\n• Al Zahraa — семейный\n• Obhur — у моря\n\n💰 Цены:\n• Однушка: от 25,000 SAR/год\n• Двушка: от 40,000 SAR/год\n• Compound villa: от 80,000 SAR/год\n\n🌐 Сайты: Bayut.sa, Aqar.fm, Haraj.com.sa", "tags": ["аренда", "районы"]},
        {"id": 2, "category": "cooking", "city": "both", "title": "Как приготовить творог дома", "content": "🛒 Ингредиенты:\n• 2 литра молока Full Fat\n• 3 ст.л. лимонного сока\n• Щепотка соли\n\n👩‍🍳 Приготовление:\n1. Нагрей молоко до 80°C\n2. Добавь лимонный сок\n3. Подожди 5 минут\n4. Откинь на марлю\n5. Дай стечь 30-60 минут\n6. Посоли по вкусу", "tags": ["рецепт", "творог"]},
        {"id": 3, "category": "docs", "city": "both", "title": "Iqama — вид на жительство", "content": "📋 Iqama — карта резидента.\n\n📝 Как получить:\n1. Работодатель подаёт документы\n2. Медосмотр\n3. Биометрия\n4. Карта через 1-3 месяца\n\n📱 Установи Absher сразу!", "tags": ["iqama", "документы"]},
        {"id": 4, "category": "tips", "city": "both", "title": "Главные лайфхаки", "content": "📱 Приложения:\n• Absher — гос. услуги\n• Careem/Uber — такси\n• Jahez — доставка еды\n• Noon — покупки\n\n🏦 Банки: Al Rajhi, SNB\n\n☀️ Лето до 45°C — гуляй вечером!", "tags": ["советы", "приложения"]},
        {"id": 5, "category": "schools", "city": "both", "title": "Международные школы", "content": "🎓 Джидда:\n• Jeddah International School\n• British International School\n\n🎓 Эр-Рияд:\n• British International School Riyadh\n• American International School\n\n💰 Стоимость: 30,000–80,000 SAR/год", "tags": ["школа", "образование"]},
    ]
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return INITIAL_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def next_id(data):
    if not data["articles"]:
        return 1
    return max(a["id"] for a in data["articles"]) + 1

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu_keyboard():
    buttons = []
    row = []
    for i, (cat_id, (icon, label)) in enumerate(CATEGORIES.items()):
        row.append(InlineKeyboardButton(f"{icon} {label}", callback_data=f"cat_{cat_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔍 Поиск", callback_data="search")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Привет, {name}!\n\n🇸🇦 Я гид для русскоязычных экспатов в Саудовской Аравии.\n\nВыбери категорию 👇",
        reply_markup=main_menu_keyboard()
    )

async def home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🇸🇦 Главное меню\n\nВыбери категорию:", reply_markup=main_menu_keyboard())

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.replace("cat_", "")
    icon, label = CATEGORIES.get(cat_id, ("📂", cat_id))
    data = load_data()
    articles = [a for a in data["articles"] if a["category"] == cat_id]
    if not articles:
        await query.edit_message_text(f"{icon} {label}\n\nПока нет статей. Скоро добавим!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="home")]]))
        return
    buttons = [[InlineKeyboardButton(f"📄 {a['title']}", callback_data=f"art_{a['id']}")] for a in articles]
    buttons.append([InlineKeyboardButton("← Главное меню", callback_data="home")])
    await query.edit_message_text(f"{icon} {label}\n\nВыбери статью:", reply_markup=InlineKeyboardMarkup(buttons))

async def article_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    art_id = int(query.data.replace("art_", ""))
    data = load_data()
    article = next((a for a in data["articles"] if a["id"] == art_id), None)
    if not article:
        await query.edit_message_text("Статья не найдена.")
        return
    icon, label = CATEGORIES.get(article["category"], ("📂", ""))
    city = CITIES.get(article["city"], "")
    tags = " ".join(f"#{t}" for t in article.get("tags", []))
    text = f"{icon} *{article['title']}*\n{city}\n{'─'*25}\n\n{article['content']}\n\n_{tags}_"
    if len(text) > 4096:
        text = text[:4090] + "..."
    buttons = [[InlineKeyboardButton(f"← {label}", callback_data=f"cat_{article['category']}")], [InlineKeyboardButton("🏠 Главное меню", callback_data="home")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

async def search_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["searching"] = True
    await query.edit_message_text("🔍 Введи слово для поиска:\n(например: квартира, творог, школа)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="home")]]))

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("searching"):
        return
    context.user_data["searching"] = False
    q = update.message.text.lower()
    data = load_data()
    results = [a for a in data["articles"] if q in a["title"].lower() or q in a["content"].lower()]
    if not results:
        await update.message.reply_text(f"По запросу «{q}» ничего не найдено.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="home")]]))
        return
    buttons = [[InlineKeyboardButton(f"📄 {a['title']}", callback_data=f"art_{a['id']}")] for a in results]
    buttons.append([InlineKeyboardButton("🏠 Меню", callback_data="home")])
    await update.message.reply_text(f"Найдено {len(results)} статей:", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа.")
        return ConversationHandler.END
    await update.message.reply_text("➕ Шаг 1/4: Введи заголовок статьи:")
    return ADD_TITLE

async def admin_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_article"] = {"title": update.message.text}
    buttons = [[InlineKeyboardButton(f"{icon} {label}", callback_data=f"newcat_{cat_id}")] for cat_id, (icon, label) in CATEGORIES.items()]
    await update.message.reply_text(f"Шаг 2/4: Выбери категорию:", reply_markup=InlineKeyboardMarkup(buttons))
    return ADD_CATEGORY

async def admin_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_article"]["category"] = query.data.replace("newcat_", "")
    buttons = [[InlineKeyboardButton(label, callback_data=f"newcity_{city_id}")] for city_id, label in CITIES.items()]
    await query.edit_message_text("Шаг 3/4: Выбери город:", reply_markup=InlineKeyboardMarkup(buttons))
    return ADD_CITY

async def admin_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_article"]["city"] = query.data.replace("newcity_", "")
    await query.edit_message_text("Шаг 4/4: Напиши текст статьи:")
    return ADD_CONTENT

async def admin_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    article = context.user_data.get("new_article", {})
    article["content"] = update.message.text
    article["tags"] = []
    data = load_data()
    article["id"] = next_id(data)
    data["articles"].append(article)
    save_data(data)
    await update.message.reply_text(f"✅ Статья добавлена!\n\n📌 {article['title']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="home")]]))
    context.user_data.pop("new_article", None)
    return ConversationHandler.END

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("new_article", None)
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END

async def list_articles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    data = load_data()
    if not data["articles"]:
        await update.message.reply_text("Статей пока нет.")
        return
    lines = [f"ID {a['id']} | {a['title']}" for a in data["articles"]]
    await update.message.reply_text("📋 Все статьи:\n\n" + "\n".join(lines) + "\n\nУдалить: /delete ID")

async def delete_article(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Использование: /delete 5")
        return
    art_id = int(args[0])
    data = load_data()
    article = next((a for a in data["articles"] if a["id"] == art_id), None)
    if not article:
        await update.message.reply_text(f"Статья {art_id} не найдена.")
        return
    data["articles"] = [a for a in data["articles"] if a["id"] != art_id]
    save_data(data)
    await update.message.reply_text(f"✅ Удалено: {article['title']}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "/start — главное меню\n/help — помощь"
    if is_admin(update.effective_user.id):
        text += "\n\n⚙️ Админ:\n/admin — добавить статью\n/list — все статьи\n/delete ID — удалить"
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(TOKEN).build()
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_start)],
        states={
            ADD_TITLE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_title)],
            ADD_CATEGORY: [CallbackQueryHandler(admin_category, pattern="^newcat_")],
            ADD_CITY:     [CallbackQueryHandler(admin_city, pattern="^newcity_")],
            ADD_CONTENT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_content)],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", list_articles))
    app.add_handler(CommandHandler("delete", delete_article))
    app.add_handler(admin_conv)
    app.add_handler(CallbackQueryHandler(home_handler, pattern="^home$"))
    app.add_handler(CallbackQueryHandler(search_prompt, pattern="^search$"))
    app.add_handler(CallbackQueryHandler(category_handler, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(article_handler, pattern="^art_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
