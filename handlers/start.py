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

    # Вопрос 2: Доход за 2025
    keyboard_q2 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="💵 До 50 000 в месяц",
                callback_data="q2_under50"
            )],
            [InlineKeyboardButton(
                text="💰 50–100 000",
                callback_data="q2_50to100"
            )],
            [InlineKeyboardButton(
                text="💎 100–300 000",
                callback_data="q2_100to300"
            )],
            [InlineKeyboardButton(
                text="🚀 300 000+",
                callback_data="q2_over300"
            )]
        ]
    )

    question_2_text = (
        "✅ Принято!\n\n"
        "Для начала зафиксируем, с чем ты входишь в 2026.\n"
        "Мне не нужны точные цифры, главное — порядок.\n\n"
        "<b>Вопрос 2. Доход за 2025</b>\n\n"
        "Примерно какой был твой средний ежемесячный доход в 2025?\n"
        "На каком уровне ты сейчас?"
    )

    await callback.message.answer(
        question_2_text,
        reply_markup=keyboard_q2,
        parse_mode='HTML'
    )


@router.callback_query(F.data.in_(["q2_under50", "q2_50to100", "q2_100to300", "q2_over300"]))
async def handle_question_2(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос 2 - Доход"""

    await callback.answer()

    # Сохраняем ответ
    answer_text = {
        "q2_under50": "До 50 000 в месяц",
        "q2_50to100": "50–100 000",
        "q2_100to300": "100–300 000",
        "q2_over300": "300 000+"
    }

    await state.update_data(question_2=answer_text[callback.data])

    # Переходим к третьему вопросу
    await state.set_state(QuizStates.question_3)

    # Вопрос 3: Цели по доходу на 2026
    keyboard_q3 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📊 Стабильно x2–x3 от того, что есть сейчас",
                callback_data="q3_x2x3"
            )],
            [InlineKeyboardButton(
                text="🚀 Резкий рывок x5–x10, готов(а) вкалывать, даже если страшно",
                callback_data="q3_x5x10"
            )],
            [InlineKeyboardButton(
                text="💎 Мечтаю про x100, но не понимаю \"как\"",
                callback_data="q3_x100"
            )],
            [InlineKeyboardButton(
                text="🌱 Хочу наконец перестать выживать и нормально жить",
                callback_data="q3_survive"
            )]
        ]
    )

    question_3_text = (
        "✅ Отлично! Зафиксировали!\n\n"
        "📍 <b>Точка Б: куда хочешь прийти в 2026?</b>\n\n"
        "Теперь давай зафиксируем, чего ты хочешь от 2026 года, чтобы сказать:\n"
        "«Да, этот год я прожил(а) не зря».\n\n"
        "<b>Вопрос 3. Цель по доходу</b>\n\n"
        "Что для тебя про рост в 2026?"
    )

    await callback.message.answer(
        question_3_text,
        reply_markup=keyboard_q3,
        parse_mode='HTML'
    )


@router.callback_query(F.data.in_(["q3_x2x3", "q3_x5x10", "q3_x100", "q3_survive"]))
async def handle_question_3(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос 3 - Цель по доходу на 2026"""

    await callback.answer()

    # Сохраняем ответ
    answer_text = {
        "q3_x2x3": "Стабильно x2–x3 от того, что есть сейчас",
        "q3_x5x10": "Резкий рывок x5–x10, готов(а) вкалывать",
        "q3_x100": "Мечтаю про x100, но не понимаю \"как\"",
        "q3_survive": "Хочу перестать выживать и нормально жить"
    }

    await state.update_data(question_3=answer_text[callback.data])

    # Инициализируем счётчики боли для диагностики
    await state.update_data(
        product_pain=0,
        traffic_pain=0,
        content_pain=0,
        sales_pain=0,
        system_pain=0
    )

    # Переходим к четвёртому вопросу
    await state.set_state(QuizStates.question_4)

    # Вопрос 4: Диагностика - Продукт
    keyboard_q4 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Да, у меня есть понятное предложение",
                callback_data="q4_clear"
            )],
            [InlineKeyboardButton(
                text="🤔 Примерно могу, но запинаюсь",
                callback_data="q4_medium"
            )],
            [InlineKeyboardButton(
                text="😵 Нет, у меня миллион идей и форматов, хочу всё и сразу",
                callback_data="q4_chaos"
            )]
        ]
    )

    question_4_text = (
        "✅ Супер! Твоя цель зафиксирована!\n\n"
        "🔍 <b>Диагностика: 5 зон, где «течёт» результат</b>\n\n"
        "Теперь проверим 5 ключевых точек, где чаще всего теряются деньги.\n"
        "Я задам по одному вопросу на каждую зону — отвечай честно.\n\n"
        "📦 <b>Блок 1. Продукт/предложение</b>\n\n"
        "<b>Вопрос 4:</b> Начнём с самого очевидного вопроса: что ты продаёшь?\n\n"
        "Представь, что я твой идеальный клиент.\n"
        "Можешь ли ты за 1–2 предложения объяснить, что именно я у тебя могу купить? "
        "Чем ты мне можешь помочь?"
    )

    await callback.message.answer(
        question_4_text,
        reply_markup=keyboard_q4,
        parse_mode='HTML'
    )


@router.callback_query(F.data.in_(["q4_clear", "q4_medium", "q4_chaos"]))
async def handle_question_4(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос 4 - Диагностика продукта"""

    await callback.answer()

    # Получаем текущие данные
    data = await state.get_data()
    product_pain = data.get('product_pain', 0)

    # Начисляем баллы боли в зависимости от ответа
    pain_points = {
        "q4_clear": 0,      # Понятное предложение - нет боли
        "q4_medium": 1,     # Запинается - средняя боль
        "q4_chaos": 2       # Каша в голове - высокая боль
    }

    product_pain += pain_points[callback.data]

    # Сохраняем обновлённый счётчик и ответ
    answer_text = {
        "q4_clear": "Да, у меня есть понятное предложение",
        "q4_medium": "Примерно могу, но запинаюсь",
        "q4_chaos": "Нет, у меня миллион идей и форматов"
    }

    await state.update_data(
        question_4=answer_text[callback.data],
        product_pain=product_pain
    )

    # Переходим к пятому вопросу
    await state.set_state(QuizStates.question_5)

    await callback.message.answer(
        "✅ Принято!\n\n"
        "<b>Вопрос 5:</b> Здесь будет следующий блок диагностики...",
        parse_mode='HTML'
    )