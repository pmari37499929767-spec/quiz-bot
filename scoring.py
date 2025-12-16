"""
Алгоритм подсчета и определения главного "похитителя X100"
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from config import (
    Zone,
    ZONE_MAX,
    ZONE_PRIORITY,
    ZONE_LABEL,
    TWIST_THRESHOLD,
    TemplateVars,
    DEFAULT_TEMPLATE,
    build_twist_message,
    build_confirmation_message,
)


@dataclass
class AnswersState:
    """Состояние ответов пользователя"""
    # Сырые баллы по зонам
    scores: Dict[Zone, int] = field(default_factory=lambda: {
        "product": 0,
        "traffic": 0,
        "content": 0,
        "sales": 0,
        "system": 0,
    })

    # Зона, которую пользователь ДУМАЕТ, что является проблемой (perceived)
    perceived_zone: Optional[Zone] = None

    # Для fallback: самая "жалобная" опция
    complaint_best: Optional[Tuple[Zone, int]] = None  # (zone, complaint_level)


def normalize_scores(scores: Dict[Zone, int]) -> Dict[Zone, float]:
    """
    Нормализация баллов (чтобы "3 в продажах" = "2 в продукте")

    Returns:
        Нормализованные баллы от 0.0 до 1.0 для каждой зоны
    """
    return {
        zone: scores[zone] / ZONE_MAX[zone]
        for zone in scores.keys()
    }


def pick_max_zone(norm_scores: Dict[Zone, float]) -> Zone:
    """
    Выбрать зону с максимальным нормализованным баллом

    При равенстве используется ZONE_PRIORITY (тай-брейк)
    """
    max_val = max(norm_scores.values())
    tied = [zone for zone, score in norm_scores.items() if score == max_val]

    # Тай-брейк: выбираем по приоритету
    for zone in ZONE_PRIORITY:
        if zone in tied:
            return zone

    # Fallback (не должно случиться)
    return tied[0]


def pick_perceived_fallback(state: AnswersState) -> Optional[Zone]:
    """
    Определить perceived зону через fallback логику

    Fallback: зона с самой "жалобной" опцией (complaint)
    """
    if state.complaint_best:
        return state.complaint_best[0]

    return None


@dataclass
class DiagnosticResult:
    """Результат диагностики"""
    bottleneck: Zone              # Главный похититель (реальный)
    perceived: Optional[Zone]     # Что человек ДУМАЕТ
    twist: bool                   # Показывать ли твист
    norm_scores: Dict[Zone, float]  # Нормализованные баллы
    raw_scores: Dict[Zone, int]   # Сырые баллы


def compute_result(state: AnswersState) -> DiagnosticResult:
    """
    Вычислить результат диагностики

    Returns:
        DiagnosticResult с главным похитителем и логикой твиста
    """
    # 1. Нормализуем баллы
    norm_scores = normalize_scores(state.scores)

    # 2. Находим реальное узкое место (bottleneck)
    bottleneck = pick_max_zone(norm_scores)

    # 3. Определяем perceived (что человек думает)
    perceived = state.perceived_zone or pick_perceived_fallback(state)

    # 4. Решаем, показывать ли твист
    twist = False
    if perceived and perceived != bottleneck:
        # Проверяем, достаточно ли разница для твиста
        diff = norm_scores[bottleneck] - norm_scores[perceived]
        twist = diff >= TWIST_THRESHOLD

    return DiagnosticResult(
        bottleneck=bottleneck,
        perceived=perceived,
        twist=twist,
        norm_scores=norm_scores,
        raw_scores=state.scores.copy(),
    )


def build_final_message(
    result: DiagnosticResult,
    template_vars: Optional[TemplateVars] = None
) -> str:
    """
    Построить финальное сообщение на основе результата

    Args:
        result: Результат диагностики
        template_vars: Переменные для шаблонизации (имя эксперта, кодовое слово и т.д.)

    Returns:
        Финальное сообщение с результатом
    """
    vars = template_vars or DEFAULT_TEMPLATE

    bottleneck_name = ZONE_LABEL[result.bottleneck]
    perceived_name = ZONE_LABEL[result.perceived] if result.perceived else None

    # ТВИСТ (когда perceived != bottleneck)
    if result.twist and perceived_name:
        return build_twist_message(bottleneck_name, perceived_name, vars)

    # ПОДТВЕРЖДЕНИЕ (когда perceived == bottleneck или нет perceived)
    return build_confirmation_message(bottleneck_name, vars)
