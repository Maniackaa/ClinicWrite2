import re
import datetime
from typing import Any

import structlog
from aiogram import Router, Bot, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    Contact,
    ReplyKeyboardRemove,
)
from aiogram.exceptions import TelegramBadRequest

from config_data.conf import conf
from handlers.states import RegistrationStates
from keyboards.keyboards import (
    get_main_menu_kb,
    get_project_kb,
    get_cancel_kb,
    get_phone_kb
)
from data.project_data import (
    WELCOME_MESSAGE,
    PROJECT_DESCRIPTION,
    REGISTRATION_SUCCESS_MESSAGE,
    ARCHIVE_VIDEOS,
    REVIEWS_VIDEOS,
    CHANNEL_PARTNERROYAL_URL,
)

logger = structlog.get_logger(__name__)
router = Router()


# Админ-команда для получения video_id
@router.message(Command("get_video_id"))
async def cmd_get_video_id(message: Message):
    """Команда для админа: подсказка как получить file_id видео."""
    if str(message.from_user.id) not in conf.tg_bot.admin_ids:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    await message.answer(
        "📹 Отправьте видео следующим сообщением — в ответ пришлю <b>file_id</b>.\n\n"
        "Этот ID впишите в <code>data/project_data.py</code> в массивы <code>ARCHIVE_VIDEOS</code> или <code>REVIEWS_VIDEOS</code>.",
        parse_mode=ParseMode.HTML
    )


@router.message(F.video)
async def admin_reply_video_id(message: Message):
    """Если админ отправил видео — отвечаем ему file_id для вставки в project_data."""
    if str(message.from_user.id) not in conf.tg_bot.admin_ids:
        return
    file_id = message.video.file_id
    logger.info(f"Админ {message.from_user.id} запросил file_id видео: {file_id[:40]}...")
    await message.answer(
        f"📋 <b>file_id видео:</b>\n<code>{file_id}</code>\n\n"
        f"Впишите в <code>data/project_data.py</code> в массивы <code>ARCHIVE_VIDEOS</code> или <code>REVIEWS_VIDEOS</code>.",
        parse_mode=ParseMode.HTML
    )


# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    """Обработчик команды /start с приветственным сообщением"""
    try:
        logger.info(f'cmd_start: пользователь {message.from_user.id} ({message.from_user.username}) {message.chat.id}')
        
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=get_main_menu_kb(),
            parse_mode=ParseMode.HTML
        )
        logger.info(f'Приветственное сообщение отправлено пользователю {message.from_user.id}')
    except Exception as e:
        logger.error(f'Ошибка в cmd_start: {e}', exc_info=True)


# Обработчик кнопки "Назад в меню"
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, bot: Bot):
    """Обработчик кнопки Назад в меню"""
    try:
        logger.info(f'back_to_menu: пользователь {callback.from_user.id}')
        
        # Если сообщение содержит фото/видео, отправляем новое сообщение вместо редактирования
        if callback.message.photo or callback.message.video:
            try:
                await callback.message.delete()
            except Exception as delete_error:
                logger.warning(f'Не удалось удалить сообщение с медиа: {delete_error}')
            
            await callback.message.answer(
                WELCOME_MESSAGE,
                reply_markup=get_main_menu_kb(),
                parse_mode=ParseMode.HTML
            )
        else:
            try:
                await callback.message.edit_text(
                    WELCOME_MESSAGE,
                    reply_markup=get_main_menu_kb(),
                    parse_mode=ParseMode.HTML
                )
            except Exception as edit_error:
                # Если не удалось отредактировать, отправляем новое сообщение
                logger.warning(f'Не удалось отредактировать сообщение, отправляем новое: {edit_error}')
                await callback.message.answer(
                    WELCOME_MESSAGE,
                    reply_markup=get_main_menu_kb(),
                    parse_mode=ParseMode.HTML
                )
        
        await callback.answer()
        logger.info(f'Главное меню показано пользователю {callback.from_user.id}')
    except Exception as e:
        logger.error(f'Ошибка в back_to_menu: {e}', exc_info=True)
        try:
            await callback.answer("Произошла ошибка", show_alert=True)
        except:
            pass


# Обработчик кнопки "Наш проект"
@router.callback_query(F.data == "menu_project")
async def menu_project(callback: CallbackQuery, bot: Bot):
    """Обработчик кнопки Наш проект - показывает текст о проекте"""
    try:
        logger.info(f'menu_project: пользователь {callback.from_user.id}')
        await callback.message.edit_text(
            PROJECT_DESCRIPTION,
            reply_markup=get_project_kb(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        logger.info(f'Информация о проекте показана пользователю {callback.from_user.id}')
    except Exception as e:
        logger.error(f'Ошибка в menu_project: {e}', exc_info=True)
        try:
            await callback.answer("Произошла ошибка", show_alert=True)
        except:
            pass


# Обработчик кнопки "Архив прошедших мероприятий"
@router.callback_query(F.data == "project_archive")
async def project_archive(callback: CallbackQuery, bot: Bot):
    """Обработчик кнопки Архив прошедших мероприятий - отправляет 2 видео"""
    try:
        logger.info(f'project_archive: пользователь {callback.from_user.id}')
        await callback.answer("Загрузка архива...")
        
        # Удаляем сообщение с кнопками
        try:
            await callback.message.delete()
        except:
            pass
        
        # Отправляем видео из архива
        videos_sent = 0
        for video_id in ARCHIVE_VIDEOS:
            if video_id:
                try:
                    await bot.send_video(
                        chat_id=callback.from_user.id,
                        video=video_id
                    )
                    videos_sent += 1
                    logger.info(f'Видео из архива отправлено: {video_id[:40]}...')
                except TelegramBadRequest as e:
                    logger.warning(f'Ошибка отправки видео из архива: {e}')
                except Exception as e:
                    logger.error(f'Ошибка при отправке видео из архива: {e}', exc_info=True)
        
        if videos_sent == 0:
            await callback.message.answer(
                "❌ Видео из архива временно недоступны.",
                reply_markup=get_project_kb()
            )
        else:
            # Отправляем меню проекта
            await callback.message.answer(
                "🔸 Наш проект\n\nВыберите раздел:",
                reply_markup=get_project_kb()
            )
        
        logger.info(f'Архив отправлен пользователю {callback.from_user.id}, отправлено видео: {videos_sent}')
    except Exception as e:
        logger.error(f'Ошибка в project_archive: {e}', exc_info=True)
        try:
            await callback.answer("Произошла ошибка", show_alert=True)
        except:
            pass


# Обработчик кнопки "Отзывы участников"
@router.callback_query(F.data == "project_reviews")
async def project_reviews(callback: CallbackQuery, bot: Bot):
    """Обработчик кнопки Отзывы участников - отправляет 2 видео"""
    try:
        logger.info(f'project_reviews: пользователь {callback.from_user.id}')
        await callback.answer("Загрузка отзывов...")
        
        # Удаляем сообщение с кнопками
        try:
            await callback.message.delete()
        except:
            pass
        
        # Отправляем видео с отзывами
        videos_sent = 0
        for video_id in REVIEWS_VIDEOS:
            if video_id:
                try:
                    await bot.send_video(
                        chat_id=callback.from_user.id,
                        video=video_id
                    )
                    videos_sent += 1
                    logger.info(f'Видео с отзывом отправлено: {video_id[:40]}...')
                except TelegramBadRequest as e:
                    logger.warning(f'Ошибка отправки видео с отзывом: {e}')
                except Exception as e:
                    logger.error(f'Ошибка при отправке видео с отзывом: {e}', exc_info=True)
        
        if videos_sent == 0:
            await callback.message.answer(
                "❌ Видео с отзывами временно недоступны.",
                reply_markup=get_project_kb()
            )
        else:
            # Отправляем меню проекта
            await callback.message.answer(
                "🔸 Наш проект\n\nВыберите раздел:",
                reply_markup=get_project_kb()
            )
        
        logger.info(f'Отзывы отправлены пользователю {callback.from_user.id}, отправлено видео: {videos_sent}')
    except Exception as e:
        logger.error(f'Ошибка в project_reviews: {e}', exc_info=True)
        try:
            await callback.answer("Произошла ошибка", show_alert=True)
        except:
            pass


# Обработчик кнопки "Регистрация на 14 марта"
@router.callback_query(F.data == "menu_registration")
async def start_registration(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Обработчик начала регистрации - запрашивает ФИО"""
    try:
        logger.info(f'start_registration: пользователь {callback.from_user.id}')
        
        await state.set_state(RegistrationStates.waiting_for_name)
        
        text = "📝 Регистрация на конференцию \"Объединяем компетенции - искусство криоконсервации\"\n\n"
        text += "Пожалуйста, введите ваше ФИО:"
        
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_cancel_kb(),
                parse_mode=ParseMode.HTML
            )
        except Exception as edit_error:
            logger.warning(f'Не удалось отредактировать сообщение, отправляем новое: {edit_error}')
            await callback.message.answer(
                text,
                reply_markup=get_cancel_kb(),
                parse_mode=ParseMode.HTML
            )
        
        await callback.answer()
        logger.info(f'Запрос ФИО отправлен пользователю {callback.from_user.id}')
    except Exception as e:
        logger.error(f'Ошибка в start_registration: {e}', exc_info=True)
        try:
            await callback.answer("Произошла ошибка", show_alert=True)
        except:
            pass
        try:
            await state.clear()
        except:
            pass


# Обработчик ввода ФИО
@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, bot: Bot, state: FSMContext):
    """Обработчик ввода ФИО - запрашивает телефон"""
    try:
        logger.info(f'process_name: пользователь {message.from_user.id}, ФИО={message.text}')
        name = message.text.strip()
        
        if len(name) < 3:
            logger.warning(f'Слишком короткое ФИО от пользователя {message.from_user.id}: {name}')
            await message.answer(
                "❌ ФИО слишком короткое. Пожалуйста, введите ваше полное ФИО еще раз:",
                reply_markup=get_cancel_kb()
            )
            return
        
        await state.update_data(client_name=name)
        await state.set_state(RegistrationStates.waiting_for_phone)
        
        text = f"✅ ФИО: <b>{name}</b>\n\n"
        text += "Теперь введите ваш номер телефона или нажмите кнопку ниже, чтобы поделиться номером:"
        
        await message.answer(
            text,
            reply_markup=get_phone_kb(),
            parse_mode=ParseMode.HTML
        )
        logger.info(f'ФИО принято: {name}, запрос телефона отправлен пользователю {message.from_user.id}')
    except Exception as e:
        logger.error(f'Ошибка в process_name: {e}', exc_info=True)
        try:
            await message.answer("Произошла ошибка. Попробуйте еще раз.")
        except:
            pass
        try:
            await state.clear()
        except:
            pass


# Обработчик получения контакта (кнопка "Поделиться телефоном")
@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_contact(message: Message, bot: Bot, state: FSMContext):
    """Обработчик получения контакта через кнопку"""
    try:
        logger.info(f'process_contact: пользователь {message.from_user.id}, контакт получен')
        contact: Contact = message.contact
        
        if not contact.phone_number:
            logger.warning(f'Контакт без номера телефона от пользователя {message.from_user.id}')
            await message.answer(
                "❌ Не удалось получить номер телефона. Пожалуйста, введите номер вручную:",
                reply_markup=get_phone_kb()
            )
            return
        
        phone = contact.phone_number
        logger.info(f'Номер телефона из контакта: {phone}')
        
        # Используем тот же обработчик для продолжения регистрации
        await process_phone_internal(message, bot, state, phone)
        
    except Exception as e:
        logger.error(f'Ошибка в process_contact: {e}', exc_info=True)
        try:
            await message.answer("Произошла ошибка. Попробуйте еще раз.", reply_markup=get_phone_kb())
        except:
            pass


# Обработчик ввода телефона (текстовый ввод)
@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, bot: Bot, state: FSMContext):
    """Обработчик ввода телефона - запрашивает email"""
    try:
        # Проверяем, не является ли это контактом (обрабатывается отдельным обработчиком)
        if message.contact:
            return
        
        logger.info(f'process_phone: пользователь {message.from_user.id}, телефон={message.text}')
        phone = message.text.strip()
        
        # Обработка кнопки "Отменить" из ReplyKeyboard
        if phone.lower() in ['отменить', '❌ отменить', 'cancel']:
            await cancel_registration_text(message, bot, state)
            return
        
        # Простая валидация телефона
        phone_clean = re.sub(r'[^\d+]', '', phone)
        if len(phone_clean) < 10:
            logger.warning(f'Некорректный телефон от пользователя {message.from_user.id}: {phone}')
            await message.answer(
                "❌ Номер телефона некорректный. Пожалуйста, введите номер еще раз или нажмите кнопку ниже:",
                reply_markup=get_phone_kb()
            )
            return
        
        await process_phone_internal(message, bot, state, phone)
        
    except Exception as e:
        logger.error(f'Ошибка в process_phone: {e}', exc_info=True)
        try:
            await message.answer("Произошла ошибка. Попробуйте еще раз.", reply_markup=get_phone_kb())
        except:
            pass
        try:
            await state.clear()
        except:
            pass


# Внутренняя функция для обработки телефона и запроса email
async def process_phone_internal(message: Message, bot: Bot, state: FSMContext, phone: str):
    """Внутренняя функция для обработки телефона и запроса email"""
    try:
        await state.update_data(client_phone=phone)
        await state.set_state(RegistrationStates.waiting_for_email)
        
        text = f"✅ Телефон: <b>{phone}</b>\n\n"
        text += "Теперь введите вашу электронную почту:"
        
        await message.answer(
            text,
            reply_markup=get_cancel_kb(),
            parse_mode=ParseMode.HTML
        )
        logger.info(f'Телефон принят: {phone}, запрос email отправлен пользователю {message.from_user.id}')
        
    except Exception as e:
        logger.error(f'Ошибка в process_phone_internal: {e}', exc_info=True)
        try:
            await message.answer("Произошла ошибка. Попробуйте еще раз.", reply_markup=get_phone_kb())
        except:
            pass
        try:
            await state.clear()
        except:
            pass


# Обработчик ввода email
@router.message(RegistrationStates.waiting_for_email)
async def process_email(message: Message, bot: Bot, state: FSMContext):
    """Обработчик ввода email - отправляет заявку в канал"""
    try:
        logger.info(f'process_email: пользователь {message.from_user.id}, email={message.text}')
        email = message.text.strip()
        
        # Обработка кнопки "Отменить" из ReplyKeyboard
        if email.lower() in ['отменить', '❌ отменить', 'cancel']:
            await cancel_registration_text(message, bot, state)
            return
        
        # Простая валидация email
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            logger.warning(f'Некорректный email от пользователя {message.from_user.id}: {email}')
            await message.answer(
                "❌ Электронная почта некорректная. Пожалуйста, введите email еще раз:",
                reply_markup=get_cancel_kb()
            )
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        client_name = data.get('client_name', 'Не указано')
        client_phone = data.get('client_phone', 'Не указан')
        
        logger.info(f'Данные регистрации: ФИО={client_name}, телефон={client_phone}, email={email}')
        
        # Формируем сообщение для канала
        registration_text = f"""📋 <b>Новая регистрация на конференцию</b>

👤 ФИО: {client_name}
📞 Телефон: {client_phone}
📧 Email: {email}
🕐 Время регистрации: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"""
        
        # Отправляем заявку в канал (используем GROUP_ID из конфига)
        try:
            channel_id = conf.tg_bot.GROUP_ID
            await bot.send_message(
                chat_id=channel_id,
                text=registration_text,
                parse_mode=ParseMode.HTML
            )
            
            # Подтверждаем пользователю
            await message.answer(
                REGISTRATION_SUCCESS_MESSAGE,
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.HTML
            )
            await message.answer(
                "Главное меню:",
                reply_markup=get_main_menu_kb()
            )
            
            logger.info(f"Регистрация отправлена: ФИО={client_name}, телефон={client_phone}, email={email}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки регистрации в канал: {e}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка при отправке регистрации. Пожалуйста, попробуйте позже или свяжитесь с нами.",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer(
                "Главное меню:",
                reply_markup=get_main_menu_kb()
            )
        
        # Очищаем состояние
        await state.clear()
        logger.info(f'Состояние FSM очищено для пользователя {message.from_user.id}')
        
    except Exception as e:
        logger.error(f'Ошибка в process_email: {e}', exc_info=True)
        try:
            await message.answer("Произошла ошибка. Попробуйте еще раз.", reply_markup=get_cancel_kb())
        except:
            pass
        try:
            await state.clear()
        except:
            pass


# Обработчик текстовой команды "Отменить" из ReplyKeyboard
async def cancel_registration_text(message: Message, bot: Bot, state: FSMContext):
    """Обработчик отмены регистрации через текстовую команду"""
    try:
        logger.info(f'cancel_registration_text: пользователь {message.from_user.id}')
        await state.clear()
        
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )
        await message.answer(
            "Главное меню:",
            reply_markup=get_main_menu_kb()
        )
        logger.info(f'Регистрация отменена пользователем {message.from_user.id}')
    except Exception as e:
        logger.error(f'Ошибка в cancel_registration_text: {e}', exc_info=True)
        try:
            await state.clear()
        except:
            pass


# Обработчик отмены регистрации
@router.callback_query(F.data == "cancel_registration")
async def cancel_registration(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Обработчик отмены регистрации на конференцию"""
    try:
        logger.info(f'cancel_registration: пользователь {callback.from_user.id}')
        await state.clear()
        
        try:
            await callback.message.edit_text(
                WELCOME_MESSAGE,
                reply_markup=get_main_menu_kb(),
                parse_mode=ParseMode.HTML
            )
        except Exception as edit_error:
            # Если не удалось отредактировать, отправляем новое
            logger.warning(f'Не удалось отредактировать сообщение при отмене, отправляем новое: {edit_error}')
            await callback.message.answer(
                WELCOME_MESSAGE,
                reply_markup=get_main_menu_kb(),
                parse_mode=ParseMode.HTML
            )
        
        await callback.answer("Регистрация отменена")
        logger.info(f'Регистрация отменена пользователем {callback.from_user.id}')
    except Exception as e:
        logger.error(f'Ошибка в cancel_registration: {e}', exc_info=True)
        try:
            await callback.answer("Произошла ошибка", show_alert=True)
        except:
            pass
        try:
            await state.clear()
        except:
            pass


# Обработчик неизвестных сообщений
@router.message(F.chat.type == 'private')
async def echo(message: Message, bot: Bot, state: FSMContext):
    """Обработчик неизвестных сообщений"""
    try:
        # Проверяем, не находится ли пользователь в состоянии FSM
        current_state = await state.get_state()
        if current_state:
            # Если пользователь в состоянии FSM, не обрабатываем сообщение здесь
            return
        
        # Игнорируем неизвестные сообщения
        logger.debug(f'Неизвестное сообщение от пользователя {message.from_user.id}: {message.text}')
    except Exception as e:
        logger.error(e, exc_info=True)
