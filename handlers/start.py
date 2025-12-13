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

    # Вопрос 5: Диагностика - Трафик
    keyboard_q5 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Новые люди стабильно приходят каждую неделю",
                callback_data="q5_stable"
            )],
            [InlineKeyboardButton(
                text="🤷 Иногда прибавляется кто-то, иногда тишина",
                callback_data="q5_unstable"
            )],
            [InlineKeyboardButton(
                text="😞 Практически одни и те же лица везде, никого нового",
                callback_data="q5_stagnant"
            )]
        ]
    )

    question_5_text = (
        "✅ Принято!\n\n"
        "👥 <b>Блок 2. Поток людей (трафик)</b>\n\n"
        "Хороший продукт без людей — это как концерт в пустом зале.\n\n"
        "<b>Вопрос 5:</b> Насколько стабильно к тебе приходят новые люди?"
    )

    await callback.message.answer(
        question_5_text,
        reply_markup=keyboard_q5,
        parse_mode='HTML'
    )


@router.callback_query(F.data.in_(["q5_stable", "q5_unstable", "q5_stagnant"]))
async def handle_question_5(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос 5 - Диагностика трафика"""

    await callback.answer()

    # Получаем текущие данные
    data = await state.get_data()
    traffic_pain = data.get('traffic_pain', 0)

    # Начисляем баллы боли в зависимости от ответа
    pain_points = {
        "q5_stable": 0,      # Стабильный трафик - нет боли
        "q5_unstable": 1,    # Нестабильный - средняя боль
        "q5_stagnant": 2     # Нет новых людей - высокая боль
    }

    traffic_pain += pain_points[callback.data]

    # Сохраняем обновлённый счётчик и ответ
    answer_text = {
        "q5_stable": "Новые люди стабильно приходят каждую неделю",
        "q5_unstable": "Иногда прибавляется кто-то, иногда тишина",
        "q5_stagnant": "Практически одни и те же лица везде, никого нового"
    }

    await state.update_data(
        question_5=answer_text[callback.data],
        traffic_pain=traffic_pain
    )

    # Переходим к шестому вопросу
    await state.set_state(QuizStates.question_6)

    # Вопрос 6: Диагностика - Контент/доверие
    keyboard_q6 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Регулярно, с понятными темами и рубриками",
                callback_data="q6_regular"
            )],
            [InlineKeyboardButton(
                text="🎨 Пишу/выступаю когда есть вдохновение и силы, как попало",
                callback_data="q6_irregular"
            )],
            [InlineKeyboardButton(
                text="📚 Часто даю пользу, но почти не веду к продукту",
                callback_data="q6_no_funnel"
            )]
        ]
    )

    # Получаем нишу пользователя для персонализации
    data = await state.get_data()
    niche = data.get('niche', 'соцсетях')

    question_6_text = (
        "✅ Зафиксировали!\n\n"
        "📝 <b>Блок 3. Контент / доверие</b>\n\n"
        "Люди покупают не только продукт, но и историю, в которую ты их зовёшь.\n\n"
        f"<b>Вопрос 6:</b> Как ты ведёшь контент в своих основных площадках?"
    )

    await callback.message.answer(
        question_6_text,
        reply_markup=keyboard_q6,
        parse_mode='HTML'
    )


@router.callback_query(F.data.in_(["q6_regular", "q6_irregular", "q6_no_funnel"]))
async def handle_question_6(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос 6 - Диагностика контента/доверия"""

    await callback.answer()

    # Получаем текущие данные
    data = await state.get_data()
    content_pain = data.get('content_pain', 0)

    # Начисляем баллы боли в зависимости от ответа
    pain_points = {
        "q6_regular": 0,       # Регулярный контент с логикой - нет боли
        "q6_irregular": 2,     # Нерегулярно, как попало - высокая боль
        "q6_no_funnel": 2      # Нет логики прогрева к продукту - высокая боль
    }

    content_pain += pain_points[callback.data]

    # Сохраняем обновлённый счётчик и ответ
    answer_text = {
        "q6_regular": "Регулярно, с понятными темами и рубриками",
        "q6_irregular": "Пишу когда есть вдохновение, как попало",
        "q6_no_funnel": "Часто даю пользу, но почти не веду к продукту"
    }

    await state.update_data(
        question_6=answer_text[callback.data],
        content_pain=content_pain
    )

    # Переходим к седьмому вопросу
    await state.set_state(QuizStates.question_7)

    # Вопрос 7: Диагностика - Продажи и офферы
    keyboard_q7 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Регулярно, мне ок с продажами. Не стесняюсь",
                callback_data="q7_regular"
            )],
            [InlineKeyboardButton(
                text="🤔 Иногда, когда уже прижало",
                callback_data="q7_sometimes"
            )],
            [InlineKeyboardButton(
                text="😳 Стыдно продавать, надеюсь, что сами догадаются и спросят",
                callback_data="q7_ashamed"
            )]
        ]
    )

    question_7_text = (
        "✅ Понял!\n\n"
        "💰 <b>Блок 4. Продажи и офферы</b>\n\n"
        "Теперь про самое «любимое» — продажи.\n\n"
        "<b>Вопрос 7:</b> Как часто ты прямо и спокойно говоришь людям:\n"
        "«Вот мой формат работы, вот стоимость, вот как записаться»?"
    )

    await callback.message.answer(
        question_7_text,
        reply_markup=keyboard_q7,
        parse_mode='HTML'
    )


@router.callback_query(F.data.in_(["q7_regular", "q7_sometimes", "q7_ashamed"]))
async def handle_question_7(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос 7 - Диагностика продаж"""

    await callback.answer()

    # Получаем текущие данные
    data = await state.get_data()
    sales_pain = data.get('sales_pain', 0)

    # Начисляем баллы боли в зависимости от ответа
    pain_points = {
        "q7_regular": 0,       # Регулярно продаёт - нет боли
        "q7_sometimes": 1,     # Иногда, когда прижало - средняя боль
        "q7_ashamed": 3        # Стыдно продавать - ЖИРНАЯ БОЛЬ
    }

    sales_pain += pain_points[callback.data]

    # Сохраняем обновлённый счётчик и ответ
    answer_text = {
        "q7_regular": "Регулярно, мне ок с продажами. Не стесняюсь",
        "q7_sometimes": "Иногда, когда уже прижало",
        "q7_ashamed": "Стыдно продавать, надеюсь, что сами догадаются"
    }

    await state.update_data(
        question_7=answer_text[callback.data],
        sales_pain=sales_pain
    )

    # Переходим к восьмому вопросу
    await state.set_state(QuizStates.question_8)

    # Вопрос 8: Диагностика - Система/ресурс
    keyboard_q8 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Распланирую и справлюсь",
                callback_data="q8_scale"
            )],
            [InlineKeyboardButton(
                text="😰 Придётся напрячься, но, наверное, как-нибудь вытяну",
                callback_data="q8_struggle"
            )],
            [InlineKeyboardButton(
                text="🔥 Сгорю, запутаюсь и начну сливать. Испорчу отношения с половиной",
                callback_data="q8_burnout"
            )]
        ]
    )

    question_8_text = (
        "✅ Зафиксировал!\n\n"
        "⚙️ <b>Блок 5. Система / ресурс</b>\n\n"
        "И ещё вопрос не про цифры, а про выживание.\n\n"
        "<b>Вопрос 8:</b> Если к тебе завтра придут 20 клиентов одновременно, что произойдёт?"
    )

    await callback.message.answer(
        question_8_text,
        reply_markup=keyboard_q8,
        parse_mode='HTML'
    )


@router.callback_query(F.data.in_(["q8_scale", "q8_struggle", "q8_burnout"]))
async def handle_question_8(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос 8 - Диагностика системы/ресурсов"""

    await callback.answer()

    # Получаем текущие данные
    data = await state.get_data()
    system_pain = data.get('system_pain', 0)

    # Начисляем баллы боли в зависимости от ответа
    pain_points = {
        "q8_scale": 0,        # Готов масштабироваться - нет боли
        "q8_struggle": 1,     # Напрячётся, но справится - средняя боль
        "q8_burnout": 2       # Сгорит и запутается - высокая боль (нет масштабируемости)
    }

    system_pain += pain_points[callback.data]

    # Сохраняем обновлённый счётчик и ответ
    answer_text = {
        "q8_scale": "Распланирую и справлюсь",
        "q8_struggle": "Придётся напрячься, но вытяну",
        "q8_burnout": "Сгорю, запутаюсь и начну сливать"
    }

    await state.update_data(
        question_8=answer_text[callback.data],
        system_pain=system_pain
    )

    # Все вопросы пройдены - переходим к результатам
    await state.set_state(QuizStates.show_result)

    await callback.message.answer(
        "✅ Отлично! Диагностика завершена.\n\n"
        "Сейчас проанализирую твои ответы и покажу результат...",
        parse_mode='HTML'
    )