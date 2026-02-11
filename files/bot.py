
"""
EcoBala Telegram Bot
Бот для экологической платформы EcoBala

Возможности:
- Регистрация и авторизация
- Просмотр квестов
- Выполнение квестов
- Проверка баланса
- Обмен баллов
- Уведомления
"""

import logging
import os
import requests
from datetime import datetime
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===========================================
# КОНФИГУРАЦИЯ
# ===========================================

# TODO: Замените на ваш токен от @BotFather
BOT_TOKEN = "8508126262:AAHeQr0ppPwrs1AjJYr0_Ouqm_6_rGI_Wt0"

# URL вашего сайта (API)
API_URL = "http://localhost/ecobala"  # Замените на ваш домен

# Контакты
INSTAGRAM = "https://www.instagram.com/ecobala.kz/"
EMAIL = "ecobalakz@gmail.com"

# Состояния для ConversationHandler
(
    REGISTER_NAME,
    REGISTER_EMAIL,
    REGISTER_PASSWORD,
    REGISTER_TYPE,
    LOGIN_EMAIL,
    LOGIN_PASSWORD,
    SUBMIT_QUEST_PHOTO,
    SUBMIT_QUEST_TEXT,
    WITHDRAW_AMOUNT,
    WITHDRAW_METHOD,
    WITHDRAW_DETAILS,
) = range(11)

# ===========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ===========================================

def make_api_request(endpoint, method='GET', data=None, files=None):
    """Отправка запроса к API"""
    url = f"{API_URL}/{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, params=data)
        elif method == 'POST':
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, data=data)
        
        return response.json()
    except Exception as e:
        logger.error(f"API Error: {e}")
        return {'success': False, 'message': str(e)}

def get_user_data(context):
    """Получить данные пользователя из контекста"""
    return context.user_data.get('user_info', None)

def is_logged_in(context):
    """Проверка авторизации"""
    return 'user_info' in context.user_data and context.user_data['user_info'] is not None

def format_points(points):
    """Форматирование баллов"""
    return f"{points:,}".replace(',', ' ')

# ===========================================
# ГЛАВНОЕ МЕНЮ И КОМАНДЫ
# ===========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = f"""
🌱 Добро пожаловать в EcoBala, {user.first_name}!

*Экологическая платформа для заботы о планете*

Выполняй эко-задания, зарабатывай баллы и делай мир чище! 🌍

📱 Instagram: [ecobala.kz]({INSTAGRAM})
📧 Email: {EMAIL}

Выберите действие:
"""
    
    keyboard = []
    
    if is_logged_in(context):
        keyboard = [
            [InlineKeyboardButton("🎯 Мои квесты", callback_data='my_quests')],
            [InlineKeyboardButton("🌟 Все квесты", callback_data='all_quests')],
            [InlineKeyboardButton("👤 Мой профиль", callback_data='profile')],
            [InlineKeyboardButton("💰 Баланс", callback_data='balance')],
            [InlineKeyboardButton("🏆 Рейтинг", callback_data='leaderboard')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🔐 Войти", callback_data='login')],
            [InlineKeyboardButton("✨ Регистрация", callback_data='register')],
            [InlineKeyboardButton("ℹ️ О проекте", callback_data='about')],
            [InlineKeyboardButton("📞 Контакты", callback_data='contacts')],
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.callback_query.message.edit_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📖 *Помощь по боту EcoBala*

*Основные команды:*
/start - Главное меню
/help - Эта справка
/profile - Мой профиль
/quests - Список квестов
/balance - Мой баланс
/leaderboard - Рейтинг пользователей

*Как это работает:*
1️⃣ Зарегистрируйтесь или войдите
2️⃣ Выберите квест из списка
3️⃣ Выполните задание
4️⃣ Загрузите фото-отчёт
5️⃣ Получите баллы после проверки
6️⃣ Обменяйте баллы на деньги

*Контакты:*
📱 Instagram: [ecobala.kz]({INSTAGRAM})
📧 Email: {EMAIL}
🌐 Сайт: {API_URL}

По всем вопросам пишите на email!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ===========================================
# РЕГИСТРАЦИЯ
# ===========================================

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "📝 *Регистрация в EcoBala*\n\nВведите ваше полное имя:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени при регистрации"""
    context.user_data['register_name'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📧 Введите ваш email:",
        reply_markup=reply_markup
    )
    
    return REGISTER_EMAIL

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение email при регистрации"""
    email = update.message.text
    
    # Простая валидация email
    if '@' not in email or '.' not in email:
        await update.message.reply_text("❌ Некорректный email. Попробуйте снова:")
        return REGISTER_EMAIL
    
    context.user_data['register_email'] = email
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔒 Придумайте пароль (минимум 6 символов):",
        reply_markup=reply_markup
    )
    
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение пароля при регистрации"""
    password = update.message.text
    
    if len(password) < 6:
        await update.message.reply_text("❌ Пароль слишком короткий. Минимум 6 символов:")
        return REGISTER_PASSWORD
    
    context.user_data['register_password'] = password
    
    keyboard = [
        [InlineKeyboardButton("👶 Я ребёнок", callback_data='type_child')],
        [InlineKeyboardButton("👦 Я подросток", callback_data='type_teen')],
        [InlineKeyboardButton("👤 Взрослый", callback_data='type_adult')],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👥 Выберите ваш тип профиля:",
        reply_markup=reply_markup
    )
    
    return REGISTER_TYPE

async def register_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор типа пользователя и завершение регистрации"""
    query = update.callback_query
    await query.answer()
    
    user_type = query.data.replace('type_', '')
    
    # Отправка запроса на регистрацию
    data = {
        'action': 'register',
        'full_name': context.user_data['register_name'],
        'email': context.user_data['register_email'],
        'password': context.user_data['register_password'],
        'user_type': user_type
    }
    
    response = make_api_request('auth.php', method='POST', data=data)
    
    if response.get('success'):
        # Сохранить данные пользователя
        context.user_data['user_info'] = response.get('user')
        
        await query.message.edit_text(
            f"✅ *Регистрация успешна!*\n\n"
            f"Добро пожаловать, {context.user_data['register_name']}! 🎉\n\n"
            f"Теперь вы можете выполнять квесты и зарабатывать баллы!",
            parse_mode='Markdown'
        )
        
        # Очистить временные данные
        for key in ['register_name', 'register_email', 'register_password']:
            context.user_data.pop(key, None)
        
        # Вернуться в главное меню
        await start(update, context)
    else:
        await query.message.edit_text(
            f"❌ Ошибка регистрации:\n{response.get('message')}\n\n"
            f"Попробуйте снова /start"
        )
    
    return ConversationHandler.END

# ===========================================
# ВХОД В СИСТЕМУ
# ===========================================

async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало входа"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "🔐 *Вход в аккаунт*\n\nВведите ваш email:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return LOGIN_EMAIL

async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение email при входе"""
    context.user_data['login_email'] = update.message.text
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔒 Введите пароль:",
        reply_markup=reply_markup
    )
    
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение пароля и вход"""
    password = update.message.text
    
    # Отправка запроса на вход
    data = {
        'action': 'login',
        'email': context.user_data['login_email'],
        'password': password
    }
    
    response = make_api_request('auth.php', method='POST', data=data)
    
    if response.get('success'):
        # Сохранить данные пользователя
        context.user_data['user_info'] = response.get('user')
        
        user = response.get('user')
        await update.message.reply_text(
            f"✅ *Вход выполнен успешно!*\n\n"
            f"Добро пожаловать, {user['name']}! 🎉",
            parse_mode='Markdown'
        )
        
        # Очистить временные данные
        context.user_data.pop('login_email', None)
        
        # Показать главное меню
        await start(update, context)
    else:
        await update.message.reply_text(
            f"❌ Ошибка входа:\n{response.get('message')}\n\n"
            f"Попробуйте снова /start"
        )
    
    return ConversationHandler.END

# ===========================================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# ===========================================

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль пользователя"""
    query = update.callback_query
    await query.answer()
    
    if not is_logged_in(context):
        await query.message.edit_text("❌ Вы не авторизованы. Используйте /start")
        return
    
    # Получить актуальные данные профиля
    response = make_api_request('api_user.php?action=profile', method='GET')
    
    if response.get('success'):
        user = response['data']
        
        profile_text = f"""
👤 *Ваш профиль*

📛 Имя: {user['full_name']}
📧 Email: {user['email']}
👥 Тип: {user['user_type']}

💎 Баллы: *{format_points(user['total_points'])}*
🏆 Ранг: *{user['rank_name']}* (уровень {user['rank_level']})

✅ Выполнено квестов: {user.get('completed_quests', 0)}

📅 Регистрация: {user['created_at'][:10]}
"""
        
        keyboard = [
            [InlineKeyboardButton("💰 Обменять баллы", callback_data='withdraw')],
            [InlineKeyboardButton("📊 История баллов", callback_data='points_history')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            profile_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await query.message.edit_text(
            f"❌ Ошибка загрузки профиля:\n{response.get('message')}"
        )

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать баланс"""
    query = update.callback_query
    await query.answer()
    
    if not is_logged_in(context):
        await query.message.edit_text("❌ Вы не авторизованы. Используйте /start")
        return
    
    response = make_api_request('api_user.php?action=profile', method='GET')
    
    if response.get('success'):
        user = response['data']
        points = user['total_points']
        
        balance_text = f"""
💰 *Ваш баланс*

🪙 Баллы: *{format_points(points)}*
💵 Эквивалент: *{format_points(points)} ₽*

Курс обмена: 1 балл = 1 рубль

Минимальная сумма для обмена: 100 баллов
"""
        
        keyboard = []
        if points >= 100:
            keyboard.append([InlineKeyboardButton("💸 Обменять на деньги", callback_data='withdraw')])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            balance_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# ===========================================
# КВЕСТЫ
# ===========================================

async def show_all_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все доступные квесты"""
    query = update.callback_query
    await query.answer()
    
    if not is_logged_in(context):
        await query.message.edit_text("❌ Вы не авторизованы. Используйте /start")
        return
    
    response = make_api_request('api_quests.php?action=list', method='GET')
    
    if response.get('success'):
        quests = response['data']
        
        if not quests:
            await query.message.edit_text(
                "📋 Пока нет доступных квестов.\n\nСкоро появятся новые задания!"
            )
            return
        
        text = "🌟 *Доступные квесты:*\n\n"
        keyboard = []
        
        for quest in quests[:10]:  # Показываем первые 10
            difficulty_emoji = {
                'easy': '🟢',
                'medium': '🟡',
                'hard': '🔴'
            }.get(quest['difficulty'], '⚪')
            
            text += f"{difficulty_emoji} *{quest['title']}*\n"
            text += f"   💎 Награда: {quest['points_reward']} баллов\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{quest['title'][:30]}...", 
                    callback_data=f"quest_{quest['id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_quest_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать детали квеста"""
    query = update.callback_query
    await query.answer()
    
    quest_id = query.data.replace('quest_', '')
    
    response = make_api_request(f'api_quests.php?action=get&id={quest_id}', method='GET')
    
    if response.get('success'):
        quest = response['data']
        
        difficulty_emoji = {
            'easy': '🟢 Легкий',
            'medium': '🟡 Средний',
            'hard': '🔴 Сложный'
        }.get(quest['difficulty'], '⚪ Обычный')
        
        category_emoji = {
            'cleaning': '🧹 Уборка',
            'planting': '🌱 Посадка',
            'recycling': '♻️ Переработка',
            'education': '📚 Обучение'
        }.get(quest['category'], '📋 Общее')
        
        text = f"""
🎯 *{quest['title']}*

📝 Описание:
{quest['description']}

💎 Награда: *{quest['points_reward']} баллов*
{difficulty_emoji}
{category_emoji}
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Начать квест", callback_data=f"start_quest_{quest_id}")],
            [InlineKeyboardButton("🔙 К списку квестов", callback_data='all_quests')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def start_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать квест"""
    query = update.callback_query
    await query.answer()
    
    quest_id = query.data.replace('start_quest_', '')
    
    data = {
        'action': 'start',
        'quest_id': quest_id
    }
    
    response = make_api_request('api_quests.php', method='POST', data=data)
    
    if response.get('success'):
        await query.message.edit_text(
            f"✅ *Квест начат!*\n\n"
            f"Выполните задание и отправьте фото-отчёт используя команду:\n"
            f"/submit {response['data']['user_quest_id']}\n\n"
            f"Или перейдите в 'Мои квесты' для загрузки отчёта.",
            parse_mode='Markdown'
        )
    else:
        await query.message.edit_text(
            f"❌ Ошибка:\n{response.get('message')}"
        )

async def show_my_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать квесты пользователя"""
    query = update.callback_query
    await query.answer()
    
    if not is_logged_in(context):
        await query.message.edit_text("❌ Вы не авторизованы. Используйте /start")
        return
    
    response = make_api_request('api_quests.php?action=my_quests', method='GET')
    
    if response.get('success'):
        quests = response['data']
        
        if not quests:
            text = "📋 У вас пока нет активных квестов.\n\nВыберите квест из списка доступных!"
            keyboard = [
                [InlineKeyboardButton("🌟 Все квесты", callback_data='all_quests')],
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ]
        else:
            text = "🎯 *Мои квесты:*\n\n"
            keyboard = []
            
            for quest in quests:
                status_emoji = {
                    'active': '🔵',
                    'pending': '🟡',
                    'completed': '✅',
                    'rejected': '❌'
                }.get(quest['status'], '⚪')
                
                status_text = {
                    'active': 'В процессе',
                    'pending': 'На проверке',
                    'completed': 'Выполнен',
                    'rejected': 'Отклонён'
                }.get(quest['status'], 'Неизвестно')
                
                text += f"{status_emoji} *{quest['title']}*\n"
                text += f"   Статус: {status_text}\n"
                text += f"   💎 {quest['points_reward']} баллов\n\n"
                
                if quest['status'] == 'active':
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📤 Отправить отчёт: {quest['title'][:20]}...",
                            callback_data=f"submit_{quest['id']}"
                        )
                    ])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# ===========================================
# РЕЙТИНГ
# ===========================================

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать рейтинг пользователей"""
    query = update.callback_query
    await query.answer()
    
    response = make_api_request('api_user.php?action=leaderboard&limit=10', method='GET')
    
    if response.get('success'):
        users = response['data']
        
        text = "🏆 *Топ-10 пользователей:*\n\n"
        
        medals = ['🥇', '🥈', '🥉']
        
        for i, user in enumerate(users, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            text += f"{medal} {user['full_name']}\n"
            text += f"   💎 {format_points(user['total_points'])} баллов\n"
            text += f"   🏆 {user['rank_name']}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# ===========================================
# ИНФОРМАЦИЯ И КОНТАКТЫ
# ===========================================

async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """О проекте"""
    query = update.callback_query
    await query.answer()
    
    about_text = f"""
🌱 *О проекте EcoBala*

EcoBala - это экологическая платформа, которая мотивирует людей заботиться об окружающей среде через выполнение интересных заданий.

*Как это работает:*
1. Выбирай квесты (уборка, посадка деревьев, переработка)
2. Выполняй задания
3. Загружай фото-отчёты
4. Получай баллы
5. Обменивай баллы на реальные деньги!

*Наша миссия:*
Сделать мир чище и зеленее, вовлекая людей через геймификацию и реальные награды.

*Контакты:*
📱 Instagram: [ecobala.kz]({INSTAGRAM})
📧 Email: {EMAIL}
🌐 Сайт: {API_URL}

Присоединяйся к нашему эко-движению! 🌍♻️
"""
    
    keyboard = [
        [InlineKeyboardButton("✨ Регистрация", callback_data='register')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        about_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Контакты"""
    query = update.callback_query
    await query.answer()
    
    contacts_text = f"""
📞 *Контакты EcoBala*

📱 *Instagram:*
{INSTAGRAM}
Подписывайтесь на наши новости и участвуйте в конкурсах!

📧 *Email:*
{EMAIL}
Пишите нам по любым вопросам!

🌐 *Веб-сайт:*
{API_URL}
Полная версия платформы с расширенными возможностями

🤝 *Сотрудничество:*
Хотите стать партнёром или спонсором эко-мероприятий? Свяжитесь с нами по email!

💡 *Предложения:*
Есть идеи для новых квестов или улучшений? Мы всегда открыты для ваших предложений!
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        contacts_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ===========================================
# ОТМЕНА И НАВИГАЦИЯ
# ===========================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text("❌ Операция отменена.")
    await start(update, context)
    
    return ConversationHandler.END

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    await start(update, context)

# ===========================================
# ОБРАБОТЧИКИ ОШИБОК
# ===========================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

# ===========================================
# ГЛАВНАЯ ФУНКЦИЯ
# ===========================================

def main():
    """Запуск бота"""
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчик регистрации
    register_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(register_start, pattern='^register$')],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
            REGISTER_TYPE: [CallbackQueryHandler(register_type, pattern='^type_')]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')]
    )
    
    # Обработчик входа
    login_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(login_start, pattern='^login$')],
        states={
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')]
    )
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Conversation handlers
    application.add_handler(register_handler)
    application.add_handler(login_handler)
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(show_profile, pattern='^profile$'))
    application.add_handler(CallbackQueryHandler(show_balance, pattern='^balance$'))
    application.add_handler(CallbackQueryHandler(show_all_quests, pattern='^all_quests$'))
    application.add_handler(CallbackQueryHandler(show_my_quests, pattern='^my_quests$'))
    application.add_handler(CallbackQueryHandler(show_quest_details, pattern='^quest_\d+$'))
    application.add_handler(CallbackQueryHandler(start_quest, pattern='^start_quest_\d+$'))
    application.add_handler(CallbackQueryHandler(show_leaderboard, pattern='^leaderboard$'))
    application.add_handler(CallbackQueryHandler(show_about, pattern='^about$'))
    application.add_handler(CallbackQueryHandler(show_contacts, pattern='^contacts$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("🤖 EcoBala Bot запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()