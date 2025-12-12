from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from .states import QuizStates

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Да, хочу расследование",
                callback_data="start_quiz"
            )],
            [InlineKeyboardButton(
                text="❌ Нет, потом как-нибудь",
                callback_data="decline_quiz"
            )]
        ]
    )
    
    text = (
        "👋 Привет, друг!\n\n"
        "<b>Твой личный детектив по итогам года готов к расследованию!</b>\n\n"
        "Если 2025 по доходу/результатам тебя не радует, давай устроим маленькое расследование: "
        "кто съедает твой рост и почему ты до сих пор не там, где мог(ла) быть.\n\n"
        "За 2–3 минуты ты увидишь своё узкое место и поймёшь, что с этим делать в 2026. Поехали?"
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия на кнопку 'Да'"""
    
    await callback.answer()
    
    text = (
        "Отлично! Прежде чем начнём расследование, представьтесь:\n\n"
        "<b>Как вас зовут?</b>"
    )
    
    await callback.message.answer(text, parse_mode='HTML')
    await state.set_state(QuizStates.waiting_for_name)


@router.callback_query(F.data == "decline_quiz")
async def decline_quiz(callback: CallbackQuery):
    """Обработчик нажатия на кнопку 'Нет'"""
    
    await callback.answer()
    
    text = (
        "Понимаю! 😊\n\n"
        "Когда будешь готов к расследованию — просто напиши /start\n\n"
        "Я буду ждать! 🕵️"
    )
    
    await callback.message.answer(text, parse_mode='HTML')


@router.message(QuizStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени пользователя"""
    
    name = message.text.strip()
    
    # Проверка: имя не должно быть пустым
    if not name or len(name) < 2:
        await message.answer(
            "Пожалуйста, введите корректное имя (минимум 2 символа):",
            parse_mode='HTML'
        )
        return
    
    # Сохраняем имя в состояние
    await state.update_data(name=name)
    
    # Ответ пользователю
    text = f"Приятно познакомиться, <b>{name}</b>! 👋"
    await message.answer(text, parse_mode='HTML')
    
    # Переходим к выбору ниши
    await state.set_state(QuizStates.waiting_for_niche)
    
    # Кнопки с выбором ниши
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="💼 Инфопродукты",
                callback_data="niche_infoproducts"
            )],
            [InlineKeyboardButton(
                text="📊 Консалтинг",
                callback_data="niche_consulting"
            )],
            [InlineKeyboardButton(
                text="🚀 Продажи",
                callback_data="niche_sales"
            )],
            [InlineKeyboardButton(
                text="💰 Бизнес",
                callback_data="niche_business"
            )],
            [InlineKeyboardButton(
                text="✍️ Другое (напишу сам)",
                callback_data="niche_custom"
            )]
        ]
    )
    
    await message.answer(
        "Теперь подскажи, в какой сфере ты работаешь?",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("niche_"))
async def process_niche_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора ниши из кнопок"""
    
    await callback.answer()
    
    # Если выбрал "Другое" - просим написать
    if callback.data == "niche_custom":
        await callback.message.answer(
            "Напиши свою сферу деятельности:",
            parse_mode='HTML'
        )
        return
    
    # Сохраняем нишу
    niches = {
        "niche_infoproducts": "инфопродуктах",
        "niche_consulting": "консалтинге",
        "niche_sales": "продажах",
        "niche_business": "бизнесе"
    }
    
    niche = niches.get(callback.data, "бизнесе")
    await state.update_data(niche=niche)
    
    # Переходим к первому вопросу
    await state.set_state(QuizStates.question_1)
    
    # Получаем имя из состояния
    data = await state.get_data()
    name = data.get('name', 'друг')
    
    # Задаём первый вопрос с подстановкой ниши
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📈 Лучше, чем предыдущие годы",
                callback_data="q1_better"
            )],
            [InlineKeyboardButton(
                text="➡️ Примерно на том же уровне",
                callback_data="q1_same"
            )],
            [InlineKeyboardButton(
                text="📉 Хуже, чем хотелось бы",
                callback_data="q1_worse"
            )]
        ]
    )
    
    question_text = (
        f"Отлично, <b>{name}</b>!\n\n"
        "Сейчас я задам тебе несколько вопросов. Это займёт всего 2 минуты.\n\n"
        "🎯 <b>Начнём с честной точки А.</b> Без чувства вины, просто факт.\n\n"
        f"<b>Вопрос 1:</b> Как ты оцениваешь свой 2025 по деньгам/результатам в <b>{niche}</b>?"
    )
    
    await callback.message.answer(question_text, reply_markup=keyboard, parse_mode='HTML')


@router.message(QuizStates.waiting_for_niche)
async def process_custom_niche(message: Message, state: FSMContext):
    """Обработка кастомной ниши (когда пользователь сам пишет)"""
    
    niche = message.text.strip().lower()
    
    if not niche or len(niche) < 3:
        await message.answer("Пожалуйста, напиши сферу деятельности (минимум 3 символа):")
        return
    
    # Добавляем предлог, если нужно
    if not niche.startswith(('в ', 'в')):
        niche = f"в сфере {niche}"
    
    await state.update_data(niche=niche)
    
    # Переходим к первому вопросу
    await state.set_state(QuizStates.question_1)
    
    # Получаем имя
    data = await state.get_data()
    name = data.get('name', 'друг')
    
    # Задаём первый вопрос
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📈 Лучше, чем предыдущие годы",
                callback_data="q1_better"
            )],
            [InlineKeyboardButton(
                text="➡️ Примерно на том же уровне",
                callback_data="q1_same"
            )],
            [InlineKeyboardButton(
                text="📉 Хуже, чем хотелось бы",
                callback_data="q1_worse"
            )]
        ]
    )
    
    question_text = (
        f"Отлично, <b>{name}</b>!\n\n"
        "Сейчас я задам тебе несколько вопросов. Это займёт всего 2 минуты.\n\n"
        "🎯 <b>Начнём с честной точки А.</b> Без чувства вины, просто факт.\n\n"
        f"<b>Вопрос 1:</b> Как ты оцениваешь свой 2025 по деньгам/результатам <b>{niche}</b>?"
    )
    
    await message.answer(question_text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data.in_(["q1_better", "q1_same", "q1_worse"]))
async def handle_question_1(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос 1"""
    
    await callback.answer()
    
    # Сохраняем ответ
    answer_text = {
        "q1_better": "Лучше, чем предыдущие годы",
        "q1_same": "Примерно на том же уровне",
        "q1_worse": "Хуже, чем хотелось бы"
    }
    
    await state.update_data(question_1=answer_text[callback.data])
    
    # Переходим ко второму вопросу
    await state.set_state(QuizStates.question_2)
    
    await callback.message.answer(
        "✅ Принято!\n\n"
        "<b>Вопрос 2:</b> Здесь будет второй вопрос...",
        parse_mode='HTML'
    )