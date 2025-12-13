from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    """Состояния для прохождения квиза"""
    
    waiting_for_name = State()
    waiting_for_niche = State()  # ← ДОБАВИЛИ для выбора ниши
    
    question_1 = State()
    question_2 = State()
    question_3 = State()
    question_4 = State()
    question_5 = State()
    question_6 = State()
    question_7 = State()
    question_8 = State()

    show_result = State()