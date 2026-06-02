from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from data.project_data import CHANNEL_PARTNERROYAL_URL, ROYAL_CLINIC_SITE_URL, ROYAL_CLINIC_CHANNEL_URL


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Создает клавиатуру главного меню"""
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text="🔸 Наш проект", callback_data="menu_project")
    )
    kb_builder.row(
        InlineKeyboardButton(text="🔸 Регистрация 14 июня Волгоград", callback_data="menu_registration")
    )
    kb_builder.row(
        InlineKeyboardButton(text="🔸 Подписаться на канал \"Объединяем компетенции\"", url=CHANNEL_PARTNERROYAL_URL)
    )
    kb_builder.row(
        InlineKeyboardButton(text="🔸 Перейти на сайт ROYAL CLINIC", url=ROYAL_CLINIC_SITE_URL)
    )
    kb_builder.row(
        InlineKeyboardButton(text="🔸 Подписаться на канал ROYAL CLINIC", url=ROYAL_CLINIC_CHANNEL_URL)
    )
    return kb_builder.as_markup()


def get_project_kb() -> InlineKeyboardMarkup:
    """Создает клавиатуру для раздела 'Наш проект'"""
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text="📹 Архив прошедших мероприятий", callback_data="project_archive")
    )
    kb_builder.row(
        InlineKeyboardButton(text="💬 Отзывы участников", callback_data="project_reviews")
    )
    kb_builder.row(
        InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")
    )
    return kb_builder.as_markup()


def get_cancel_kb() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой отмены"""
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_registration")
    )
    return kb_builder.as_markup()


def get_phone_kb() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с кнопкой поделиться телефоном"""
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(
        KeyboardButton(text="📱 Поделиться телефоном", request_contact=True)
    )
    kb_builder.row(
        KeyboardButton(text="❌ Отменить")
    )
    return kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
