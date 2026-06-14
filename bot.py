#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import smtplib
import logging
from email.message import EmailMessage
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN, YOUR_TELEGRAM_ID, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, SMTP_SERVER, SMTP_PORT

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

QUESTIONS = [
    (1, "1️⃣ Тип дома и состояние квартиры:\n\n▪️ Новостройка без отделки (бетонные стены)\n▪️ Новостройка с предчистовой отделкой\n▪️ Вторичное жилье (капитальный ремонт)\n▪️ Вторичное жилье (косметический ремонт, инженерия частично меняется)", 'single'),
    (2, "2️⃣ Площадь квартиры:\n\n▪️ До 60 м²\n▪️ 60 – 120 м²\n▪️ Более 120 м²", 'single'),
    (3, "3️⃣ Наличие плана БТИ (поэтажный план с экспликацией):\n\n▪️ Да, есть актуальный план БТИ (могу прислать файл или фото)\n▪️ План БТИ утерян / не заказывал, но готов заказать самостоятельно\n▪️ Плана нет\n▪️ Не уверен, нужен ли план БТИ для моей задачи", 'single'),
    (4, "4️⃣ Планируется ли перепланировка (снос/возведение стен)?\n\n▪️ Да, планируем менять конфигурацию помещений\n▪️ Только демонтаж встроенных шкафов/антресолей\n▪️ Нет, все стены остаются на месте", 'single'),
    (5, "5️⃣ Где планируется разместить электрический щиток?\n\n▪️ В прихожей (скрыто в нише)\n▪️ В отдельном техническом шкафу\n▪️ Оставить на существующем месте\n▪️ Нужен совет проектировщика", 'single'),
    (6, "6️⃣ Какие сценарии освещения хотите реализовать? (можно выбрать несколько)\n\n▪️ Одна люстра/светильник по центру комнаты\n▪️ Раздельное верхнее и локальное освещение (бра, торшеры, подсветка)\n▪️ Трековые системы на шинопроводах\n▪️ Светодиодная подсветка (ниши, шторы, карнизы, плинтус)\n▪️ Полноценная система «Умный свет» с диммированием", 'multi'),
    (7, "7️⃣ Укажите особенности по розеткам и выключателям:\n\n▪️ Стандартное размещение\n▪️ Европейский стандарт (выключатели на 90 см, розетки — 30 см)\n▪️ Индивидуальные пожелания (розетки на уровне столешниц, скрытые в полу/мебели)", 'single'),
    (8, "8️⃣ Предусмотреть выделенные линии для мощной техники? (можно выбрать несколько)\n\n▪️ Электроплита / варочная панель\n▪️ Духовой шкаф (отдельно)\n▪️ Стиральная и сушильная машины\n▪️ Электрический теплый пол\n▪️ Электрокамин / сауна (если есть)\n▪️ Зарядка для электромобиля (в паркинге / с выделенной линией из квартиры)\n▪️ Затрудняюсь ответить", 'multi'),
    (9, "9️⃣ Сколько и где нужно ТВ-точек (телевизионная розетка)?\n\n▪️ Только в гостиной\n▪️ Гостиная + каждая спальня\n▪️ Кухня + гостиная + спальни\n▪️ Не планирую телевидение, только интернет\n▪️ Затрудняюсь ответить", 'single'),
    (10, "🔟 Нужна ли структурированная сеть (интернет)?\n\n▪️ Wi-Fi роутер в прихожей (без проводов)\n▪️ Слаботочный шкаф с коммутатором и розетками в каждой комнате\n▪️ Только оптоволоконный ввод, дальше по Wi-Fi", 'single'),
    (11, "1️⃣1️⃣ Системы безопасности и контроля: (можно выбрать несколько)\n\n▪️ Домофон (аудио / видео) — разместить у входа\n▪️ Сигнализация (охранная) — датчики открытия, движения\n▪️ Видеонаблюдение внутри квартиры / на этаже\n▪️ Контроль протечек воды (датчики с кранами на стояках)\n▪️ Ничего не нужно", 'multi'),
    (12, "1️⃣2️⃣ Какая система отопления закладывается?\n\n▪️ Центральное (от радиаторов стояков)\n▪️ Центральное + электрические теплые полы в отдельных зонах\n▪️ Полный переход на водяные теплые полы (с узлом распределения)\n▪️ Автономное (свой котел) — нужна схема котельной", 'single'),
    (13, "1️⃣3️⃣ Где обязательно нужен теплый пол? (можно выбрать несколько)\n\n▪️ Ванная / санузел\n▪️ Кухня-гостиная\n▪️ Прихожая / коридор\n▪️ Балкон / лоджия (присоединенная)\n▪️ Нигде не нужен", 'multi'),
    (14, "1️⃣4️⃣ Особенности водоснабжения: (можно выбрать несколько)\n\n▪️ Скрытая разводка (коллекторная, трубы в стяжке/стенах)\n▪️ Нужен полотенцесушитель (водяной от стояка / электрический)\n▪️ Установка бойлера косвенного нагрева или накопительного водонагревателя\n▪️ Фильтры грубой и тонкой очистки на вводе (магистральные)\n▪️ Ничего менять не планирую", 'multi'),
    (15, "1️⃣5️⃣ Как планируете охлаждать воздух?\n\n▪️ Сплит-системы (настенные) — нужны трассы и дренаж\n▪️ Мультисплит-система (один наружный блок, несколько внутренних)\n▪️ Канальный кондиционер (скрытый за подшивным потолком)\n▪️ Кондиционирование не нужно", 'single'),
    (16, "1️⃣6️⃣ Требуется ли принудительная вентиляция? (можно выбрать несколько)\n\n▪️ Только естественная (вытяжка в санузлах и на кухне)\n▪️ Принудительная вытяжка с канальными вентиляторами в санузлах\n▪️ Приточно-вытяжная установка (бризеры или центральная ПВУ) с фильтрацией/без\n▪️ Кухонная вытяжка с отводом в вентканал (нужна трасса)", 'multi'),
    (17, "1️⃣7️⃣ Укажите размещение сантехники (по помещениям): (можно выбрать несколько)\n\n▪️ Унитаз (обычный / подвесной с инсталляцией)\n▪️ Раковина (накладная / врезная / с тумбой)\n▪️ Ванна (отдельностоящая / стандартная)\n▪️ Душевая кабина (с поддоном / трап в полу)\n▪️ Биде / гигиенический душ\n▪️ Стиральная машина (в ванной / на кухне / в постирочной)\n▪️ Сушильная машина\n▪️ Кухонная мойка (одна / двойная / с измельчителем)", 'multi'),
    (18, "1️⃣8️⃣ Как должны быть проложены трубы канализации и водоснабжения?\n\n▪️ Скрыто в коробах с лючками\n▪️ Замоноличены в стены/стяжку\n▪️ Открытый монтаж (не принципиально)\n▪️ Затрудняюсь ответить", 'single'),
    (19, "1️⃣9️⃣ Какой тип стяжки пола планируется?\n\n▪️ Обычная цементно-песчаная (мокрая)\n▪️ Полусухая стяжка\n▪️ Сухая сборная стяжка (Кнауф)\n▪️ Регулируемые лаги / фанера\n▪️ Не планирую", 'single'),
    (20, "2️⃣0️⃣ Потолки:\n\n▪️ Натяжные (нужны закладные под светильники и карнизы)\n▪️ Гипсокартонные\n▪️ Оштукатуренный бетон (без опуска)\n▪️ Комбинированные", 'single'),
    (21, "2️⃣1️⃣ Важны ли звукоизоляция пола и стен?\n\n▪️ Да, по максимуму (плавающий пол, звукоизолирующие панели на стены)\n▪️ Только в спальне\n▪️ Только межкомнатные перегородки\n▪️ Нет, не критично", 'single'),
    (22, "2️⃣2️⃣ Есть ли что-то нестандартное, что нужно учесть в проекте?\n\n(Напишите текстом)", 'free'),
    (23, "2️⃣3️⃣ Ваши контактные данные:\n\n▪️ Город:\n▪️ Имя:\n▪️ Телефон:\n▪️ Telegram:\n▪️ Email:", 'free'),
    (24, "2️⃣4️⃣ Адрес объекта:", 'free'),
]

def make_single_keyboard(options_text):
    lines = options_text.strip().split('\n')
    options = []
    for line in lines:
        line = line.strip()
        if line and (line.startswith('▪️') or line.startswith('-') or (line and line[0].isdigit())):
            clean = line.lstrip('▪️- ').strip()
            if clean:
                options.append(clean)
    if not options:
        options = [l.strip() for l in lines if l.strip()]
    keyboard = [options[i:i+2] for i in range(0, len(options), 2)]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def extract_options(question_text):
    lines = question_text.split('\n')
    opts = []
    for line in lines:
        line = line.strip()
        if line.startswith('▪️'):
            opts.append(line[2:].strip())
    return opts

async def send_email_report(user_data):
    text = "📋 Анкета по квартире\n\n"
    for step, q_text, _ in QUESTIONS:
        answer = user_data.get(step, "—")
        short_q = q_text.split('\n')[0][:80]
        text += f"{short_q}:\n{answer}\n\n"
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "Новая анкета квартиры"
    msg.set_content(text)
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("Письмо отправлено")
    except Exception as e:
        logging.error(f"Ошибка почты: {e}")

async def send_telegram_copy(update, context, user_data):
    report_lines = ["✅ Ваши ответы на анкету:"]
    for step, q_text, _ in QUESTIONS:
        answer = user_data.get(step, "—")
        header = q_text.split('\n')[0][:60]
        report_lines.append(f"{header}: {answer}")
    report = "\n\n".join(report_lines)
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=report)
    if YOUR_TELEGRAM_ID:
        await context.bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=f"📬 Новая анкета от @{update.effective_user.username or 'Пользователь'}\n\n{report}"
        )

async def show_multi_question(update, context, step, q_text):
    options = extract_options(q_text)
    if 'multi_selected' not in context.user_data:
        context.user_data['multi_selected'] = {}
    if step not in context.user_data['multi_selected']:
        context.user_data['multi_selected'][step] = [False] * len(options)
    selected = context.user_data['multi_selected'][step]
    keyboard = []
    for i, opt in enumerate(options):
        status = "✅" if selected[i] else "⬜"
        keyboard.append([InlineKeyboardButton(f"{status} {opt}", callback_data=f"multi_{step}_{i}")])
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data=f"multi_done_{step}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=q_text, reply_markup=reply_markup)

async def start(update, context):
    await update.message.reply_text("Привет! Я задам 24 вопроса для проектирования квартиры. Для отмены /cancel.")
    context.user_data.clear()
    context.user_data['current_step'] = 1
    await ask_current_question(update, context)

async def ask_current_question(update, context):
    step = context.user_data.get('current_step')
    if not step or step > len(QUESTIONS):
        await finish_survey(update, context)
        return
    _, q_text, q_type = QUESTIONS[step-1]
    if q_type == 'single':
        parts = q_text.split('\n\n', 1)
        options_part = parts[1] if len(parts) > 1 else q_text
        reply_markup = make_single_keyboard(options_part)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=q_text, reply_markup=reply_markup)
    elif q_type == 'multi':
        await context.bot.send_message(chat_id=update.effective_chat.id, text="(Выберите несколько вариантов, затем нажмите 'Готово')")
        await show_multi_question(update, context, step, q_text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=q_text + "\n(Введите ваш ответ текстом)", reply_markup=ReplyKeyboardRemove())

async def handle_message(update, context):
    step = context.user_data.get('current_step')
    if not step:
        await update.message.reply_text("Начните с /start")
        return
    if step > len(QUESTIONS):
        await finish_survey(update, context)
        return
    _, _, q_type = QUESTIONS[step-1]
    if q_type == 'multi':
        await update.message.reply_text("Пожалуйста, используйте кнопки для выбора вариантов и нажмите 'Готово'.")
        return
    context.user_data[step] = update.message.text
    next_step = step + 1
    context.user_data['current_step'] = next_step
    await ask_current_question(update, context)

async def handle_multi_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    step = context.user_data.get('current_step')
    if not step:
        return
    _, q_text, _ = QUESTIONS[step-1]
    options = extract_options(q_text)
    if data.startswith("multi_done_"):
        selected = context.user_data.get('multi_selected', {}).get(step, [])
        answer = ", ".join([opt for i, opt in enumerate(options) if i < len(selected) and selected[i]]) if any(selected) else "Ничего не выбрано"
        context.user_data[step] = answer
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Ответ сохранён!")
        context.user_data.pop('multi_selected', None)
        next_step = step + 1
        context.user_data['current_step'] = next_step
        await ask_current_question(update, context)
        return
    elif data.startswith("multi_"):
        parts = data.split("_")
        idx_option = int(parts[2])
        if 'multi_selected' not in context.user_data:
            context.user_data['multi_selected'] = {}
        if step not in context.user_data['multi_selected']:
            context.user_data['multi_selected'][step] = [False] * len(options)
        context.user_data['multi_selected'][step][idx_option] = not context.user_data['multi_selected'][step][idx_option]
        selected = context.user_data['multi_selected'][step]
        keyboard = []
        for i, opt in enumerate(options):
            status = "✅" if selected[i] else "⬜"
            keyboard.append([InlineKeyboardButton(f"{status} {opt}", callback_data=f"multi_{step}_{i}")])
        keyboard.append([InlineKeyboardButton("✅ Готово", callback_data=f"multi_done_{step}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return

async def finish_survey(update, context):
    user_data = {k: v for k, v in context.user_data.items() if isinstance(k, int)}
    await send_email_report(user_data)
    await send_telegram_copy(update, context, user_data)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🎉 Спасибо! Анкета успешно отправлена.\nМы свяжемся с вами.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()

async def cancel(update, context):
    await update.message.reply_text("❌ Опрос отменён.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cancel', cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_multi_callback))
    print("✅Бот для анкеты квартиры (24 вопроса) запускается...")
    application.run_polling(poll_interval=1.0, timeout=30)

if __name__ == "__main__":
    main()
