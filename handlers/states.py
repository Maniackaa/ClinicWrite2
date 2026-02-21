"""
FSM состояния для регистрации на конференцию
"""
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния для процесса регистрации на конференцию"""
    waiting_for_name = State()  # Ожидание ввода ФИО
    waiting_for_phone = State()  # Ожидание ввода телефона
    waiting_for_email = State()  # Ожидание ввода email
