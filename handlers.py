from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import add_user, get_user, delete_user, get_all_users
from keyboards import get_course_keyboard, get_confirm_keyboard, get_navigation_keyboard, get_tags_keyboard, TAGS
from utils import send_message_and_delete_command, replace_message

router = Router()

class ProfileCreation(StatesGroup):
    awaiting_photo = State()
    awaiting_skills = State()
    awaiting_tags = State()

class FindUsers(StatesGroup):
    awaiting_tags = State()

def _parse_tags_str(tags_str: str | None) -> set[str]:
    if not tags_str:
        return set()
    return {t.strip() for t in tags_str.split(",") if t.strip()}

def _format_tags(tags: set[str] | list[str] | None) -> str:
    if not tags:
        return "Не указаны"
    return ", ".join(sorted(tags))

# --------------------- КОМАНДЫ ---------------------
@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await send_message_and_delete_command(
        message,
        "👋 Добро пожаловать в бот для поиска команды УрФУ!\nВыберите ваш курс обучения:",
        keyboard=get_course_keyboard()
    )

@router.message(F.text == "/help")
async def help_command(message: Message):
    await send_message_and_delete_command(
        message,
        "📚 Команды бота:\n"
        "/start - Начать работу с ботом\n"
        "/profile - Просмотреть или отредактировать анкету\n"
        "/search - Просмотреть анкеты других пользователей\n"
        "/delete_profile - Удалить свою анкету\n"
        "/help - Показать эту справку"
    )

@router.message(F.text == "/profile")
async def profile_command(message: Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)

    if user_data:
        text = (
            f"📌 Ваша анкета:\n"
            f"👤 @{user_data['username']}\n"
            f"📚 Курс: {user_data['course']}\n"
            f"📝 Описание: {user_data['skills'] or 'Не указано'}\n"
            f"🛠 Навыки: {_format_tags(_parse_tags_str(user_data['tags']))}\n"
        )
        if user_data['photo_id']:
            await send_message_and_delete_command(message, text, keyboard=get_confirm_keyboard(), photo_id=user_data['photo_id'])
        else:
            await send_message_and_delete_command(message, text, keyboard=get_confirm_keyboard())
    else:
        await send_message_and_delete_command(message, "У вас нет анкеты. Создайте её с помощью /start.")

@router.message(F.text == "/delete_profile")
async def delete_profile_command(message: Message):
    user_id = message.from_user.id
    delete_user(user_id)
    await send_message_and_delete_command(message, "Ваша анкета удалена.")

@router.message(F.text == "/search")
async def search_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    me = get_user(user_id)
    my_tags = _parse_tags_str(me['tags'] if me else None)

    users = get_all_users(user_id)
    if not users:
        await send_message_and_delete_command(message, "Анкеты закончились. Попробуйте позже!")
        return

    # Сортировка по количеству совпадающих навыков (тегов) — убывание
    def overlap_count(u):
        their_tags = _parse_tags_str(u['tags'])
        return len(my_tags & their_tags)

    users_sorted = sorted(users, key=lambda u: overlap_count(u), reverse=True)

    await state.update_data(search_users=users_sorted, search_index=0, my_tags=list(my_tags))
    await show_user_profile(message, state, 0)
# ----------------------------------------------------

@router.message(F.text == "/find")
async def find_command(message: Message, state: FSMContext):
    await state.update_data(selected_tags=[])
    await send_message_and_delete_command(
        message,
        "🧭 Выберите навыки для поиска:",
        keyboard=get_tags_keyboard([], confirm_text="🔎 Найти", confirm_callback="find_confirm")
    )
    await state.set_state(FindUsers.awaiting_tags)
# ----------------------------------------------------

# --------------------- ПОКАЗ АНКЕТ ---------------------
async def show_user_profile(message: Message | CallbackQuery, state: FSMContext, index: int):
    data = await state.get_data()
    users = data.get("search_users", [])
    if not users or index < 0 or index >= len(users):
        target = message.message if isinstance(message, CallbackQuery) else message
        await target.answer("Анкеты закончились. Попробуйте позже!") if isinstance(message, CallbackQuery) else message.answer("Анкеты закончились. Попробуйте позже!")
        return

    current_user_tags = set(data.get("my_tags", []))
    user = users[index]
    their_tags = _parse_tags_str(user['tags'])
    matched = current_user_tags & their_tags
    text = (
        f"👤 @{user['username']}\n"
        f"📚 Курс: {user['course']}\n"
        f"🛠 Навыки: {_format_tags(their_tags)}\n"
    )
    if matched:
        text += f"✨ Совпавшие навыки: {_format_tags(matched)}\n"
    text += f"📝 Описание: {user['skills'] or 'Не указано'}\n"

    keyboard = get_navigation_keyboard(index, len(users))

    if isinstance(message, CallbackQuery):
        await replace_message(message.bot, message, new_text=text, keyboard=keyboard, photo_id=user['photo_id'] if user['photo_id'] else None)
    else:
        if user['photo_id']:
            await send_message_and_delete_command(message, text, keyboard=keyboard, photo_id=user['photo_id'])
        else:
            await send_message_and_delete_command(message, text, keyboard=keyboard)
# ----------------------------------------------------

# --------------------- CALLBACK ---------------------
@router.callback_query()
async def button_callback(callback: CallbackQuery, state: FSMContext):
    data_cb = callback.data
    await callback.answer()

    # Выбор курса
    if data_cb.startswith("course_"):
        course = {
            "course_1": "1 курс",
            "course_2": "2 курс",
            "course_3": "3 курс",
            "course_4": "4 курс",
            "course_master": "Магистратура",
            "course_phd": "Аспирантура",
        }[data_cb]

        await state.update_data(course=course, user_id=callback.from_user.id, username=callback.from_user.username)

        await replace_message(
            bot=callback.bot,
            callback=callback,
            new_text="📷 Отправьте ваше фото (или напишите /skip для пропуска):"
        )
        await state.set_state(ProfileCreation.awaiting_photo)
        return

    # Подтверждение анкеты
    if data_cb == "confirm_profile":
        data_state = await state.get_data()
        add_user(
            data_state["user_id"],
            data_state["username"],
            data_state.get("course"),
            data_state.get("photo_id"),
            data_state.get("skills"),
            data_state.get("tags")
        )
        await replace_message(callback.bot, callback, "✅ Анкета сохранена! Используйте /search для просмотра других анкет.")
        await state.clear()
        return

    # Редактирование анкеты
    if data_cb == "edit_profile":
        await replace_message(
            bot=callback.bot,
            callback=callback,
            new_text="✏ Хотите изменить анкету? Выберите курс заново:",
            keyboard=get_course_keyboard()
        )
        await state.clear()
        return

    # Навигация по анкетам
    if data_cb.startswith("nav_"):
        action, index = data_cb.split("_")[1], int(data_cb.split("_")[2])
        new_index = index - 1 if action == "prev" else index + 1
        await state.update_data(search_index=new_index)
        await show_user_profile(callback, state, new_index)
        return

    # Навыки (теги) — переключение без удаления сообщения
    if data_cb.startswith("tag_"):
        tag = data_cb.split("tag_")[1]
        cur = await state.get_data()
        selected = set(cur.get("selected_tags", []))
        if tag in selected:
            selected.remove(tag)
        else:
            if tag in TAGS:
                selected.add(tag)
        await state.update_data(selected_tags=list(selected))

        current_state = await state.get_state()
        is_find = current_state == FindUsers.awaiting_tags.state
        confirm_text = "🔎 Найти" if is_find else "✅ Подтвердить"
        confirm_cb = "find_confirm" if is_find else "tags_confirm"

        await callback.message.edit_reply_markup(
            reply_markup=get_tags_keyboard(list(selected), confirm_text=confirm_text, confirm_callback=confirm_cb)
        )
        return

    # Навыки (теги) — подтверждение
    if data_cb == "tags_confirm":
        cur = await state.get_data()
        selected = set(cur.get("selected_tags", []))
        await state.update_data(tags=",".join(sorted(selected)))

        data_state = await state.get_data()
        text = (
            f"📌 Ваша анкета:\n"
            f"👤 @{data_state['username']}\n"
            f"📚 Курс: {data_state['course']}\n"
            f"📝 Описание: {data_state.get('skills') or 'Не указано'}\n"
            f"🛠 Навыки: {_format_tags(selected)}\n"
        )

        if data_state.get("photo_id"):
            await replace_message(callback.bot, callback, new_text=text, keyboard=get_confirm_keyboard(), photo_id=data_state["photo_id"])
        else:
            await replace_message(callback.bot, callback, new_text=text, keyboard=get_confirm_keyboard())
        # Сбрасываем состояние, но данные остаются до подтверждения
        await state.set_state(None)
        return

    # Поиск по выбранным навыкам
    if data_cb == "find_confirm":
        cur = await state.get_data()
        my_selected = set(cur.get("selected_tags", []))

        if not my_selected:
            await callback.answer("Выберите хотя бы один навык", show_alert=True)
            return

        all_users = get_all_users(callback.from_user.id)

        def overlap(u):
            their = _parse_tags_str(u['tags'])
            return len(my_selected & their)

        users_filtered = [u for u in all_users if overlap(u) > 0]
        users_sorted = sorted(users_filtered, key=lambda u: overlap(u), reverse=True)

        if not users_sorted:
            await replace_message(callback.bot, callback, "Никого не найдено по выбранным навыкам. Попробуйте изменить набор навыков.")
            await state.set_state(None)
            return

        await state.update_data(search_users=users_sorted, search_index=0, my_tags=list(my_selected))
        await show_user_profile(callback, state, 0)
        await state.set_state(None)
        return
# ----------------------------------------------------

# --------------------- ФОТО + ОПИСАНИЕ + НАВЫКИ ---------------------
@router.message(ProfileCreation.awaiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)
    await send_message_and_delete_command(message, "📝 Пару слов про себя (до 500 символов):")
    await state.set_state(ProfileCreation.awaiting_skills)

@router.message(ProfileCreation.awaiting_photo, F.text == "/skip")
async def skip_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=None)
    await send_message_and_delete_command(message, "📝 Пару слов про себя (до 500 символов):")
    await state.set_state(ProfileCreation.awaiting_skills)

@router.message(ProfileCreation.awaiting_skills, F.text)
async def handle_skills(message: Message, state: FSMContext):
    skills = message.text[:500]
    await state.update_data(skills=skills, selected_tags=[])
    await send_message_and_delete_command(
        message,
        "🛠 Выберите навыки:",
        keyboard=get_tags_keyboard([])
    )
    await state.set_state(ProfileCreation.awaiting_tags)
# ----------------------------------------------------
