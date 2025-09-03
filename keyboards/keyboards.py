from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Union, List

TAGS = [
    "web", "ux/ui", "management", "backend", "frontend", "ml", "data", "cloud",
    "android", "ios", "gamedev", "devops", "security", "python",
    "js", "c++", "c#", "java"
]

def get_course_keyboard():
    """Клавиатура для выбора курса."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 курс", callback_data="course_1"),
            InlineKeyboardButton(text="2 курс", callback_data="course_2"),
        ],
        [
            InlineKeyboardButton(text="3 курс", callback_data="course_3"),
            InlineKeyboardButton(text="4 курс", callback_data="course_4"),
        ],
        [
            InlineKeyboardButton(text="Магистратура", callback_data="course_master"),
            InlineKeyboardButton(text="Аспирантура", callback_data="course_phd"),
        ],
    ])
    return keyboard

def get_confirm_keyboard():
    """Клавиатура для подтверждения анкеты."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_profile"),
            InlineKeyboardButton(text="✏ Редактировать", callback_data="edit_profile"),
        ]
    ])
    return keyboard

def get_navigation_keyboard(current_index, total):
    """Клавиатура для навигации по анкетам."""
    keyboard = []
    if current_index > 0:
        keyboard.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"nav_prev_{current_index}"))
    if current_index < total - 1:
        keyboard.append(InlineKeyboardButton(text="Вперед ➡", callback_data=f"nav_next_{current_index}"))
    return InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None

def get_tags_keyboard(
    selected: Union[List[str], None] = None,
    confirm_text: str = "✅ Подтвердить",
    confirm_callback: str = "tags_confirm"
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора тегов с возможностью переключения."""
    selected = set(selected or [])
    rows = []
    row = []
    for i, tag in enumerate(TAGS, start=1):
        active = tag in selected
        text = f"{'✅ ' if active else ''}{tag}"
        row.append(InlineKeyboardButton(text=text, callback_data=f"tag_{tag}"))
        if i % 3 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=confirm_text, callback_data=confirm_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_commands_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура со списком команд."""
    commands = [
        ("🚀 Начать (/start)", "command_start"),
        ("👤 Моя анкета (/profile)", "command_profile"),
        ("🔎 Поиск (/search)", "command_search"),
        ("🧭 Найти по навыкам (/find)", "command_find"),
        ("🗑 Удалить анкету (/delete_profile)", "command_delete_profile"),
        ("📚 Справка (/help)", "command_help"),
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=callback)] for text, callback in commands
    ])
    return keyboard