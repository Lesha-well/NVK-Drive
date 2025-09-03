from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import add_user, get_user, delete_user, get_all_users
from keyboards.keyboards import get_course_keyboard, get_confirm_keyboard, get_navigation_keyboard, get_tags_keyboard, get_commands_menu_keyboard, TAGS
from typing import Union, Set, List

router = Router()

class ProfileCreation(StatesGroup):
    awaiting_photo = State()
    awaiting_skills = State()
    awaiting_tags = State()

class FindUsers(StatesGroup):
    awaiting_tags = State()

def _parse_tags_str(tags_str: Union[str, None]) -> Set[str]:
    if not tags_str:
        return set()
    return {t.strip() for t in tags_str.split(",") if t.strip()}

def _format_tags(tags: Union[Set[str], List[str], None]) -> str:
    if not tags:
        return "Не указаны"
    return ", ".join(sorted(tags))

# --------------------- КОМАНДЫ ---------------------
@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в бот для поиска команды УрФУ!\nВыберите ваш курс обучения:",
        reply_markup=get_course_keyboard()
    )

@router.message(F.text == "/help")
async def help_command(message: Message):
    await message.answer(
        "📚 Команды бота:\n"
        "/start - Начать работу с ботом\n"
        "/profile - Просмотреть или отредактировать анкету\n"
        "/search - Просмотреть анкеты других пользователей\n"
        "/delete_profile - Удалить свою анкету\n"
        "/help - Показать эту справку"
    )


@router.message(F.text == "/profile")
async def profile_command(message: Message):
    """Обработчик команды /profile."""
    user_id = message.from_user.id
    user_data = get_user(user_id)

    if user_data:
        text = (
            f"📌 Ваша анкета:\n"
            f"👤 @{user_data[1]}\n"
            f"📚 Курс: {user_data[2]}\n"
            f"🛠 Навыки: {user_data[4] or 'Не указаны'}\n"
        )
        if user_data[3]:  # photo_id
            await message.answer_photo(user_data[3], caption=text, reply_markup=get_confirm_keyboard())
        else:
            await message.answer(text, reply_markup=get_confirm_keyboard())
    else:
        await message.answer("У вас нет анкеты. Создайте её с помощью /start.")

@router.message(F.text == "/delete_profile")
async def delete_profile_command(message: Message):
    """Обработчик команды /delete_profile."""
    user_id = message.from_user.id
    delete_user(user_id)
    await message.answer("Ваша анкета удалена.")

@router.message(F.text == "/search")
async def search_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    me = get_user(user_id)
    my_tags = _parse_tags_str(me['tags'] if me else None)

    users = get_all_users(user_id)
    if not users:
        await message.answer("Анкеты закончились. Попробуйте позже!")
        return

    users_sorted = sorted(users, key=lambda u: len(my_tags & _parse_tags_str(u['tags'])), reverse=True)
    await state.update_data(search_users=users_sorted, search_index=0, my_tags=list(my_tags))
    await show_user_profile(message, state, 0)

@router.message(F.text == "/find")
async def find_command(message: Message, state: FSMContext):
    await state.update_data(selected_tags=[])
    await message.answer(
    "🧭 Выберите навыки для поиска:",
    reply_markup=get_tags_keyboard([], confirm_text="🔎 Найти", confirm_callback="find_confirm")
)
    await state.set_state(FindUsers.awaiting_tags)

@router.message(F.text == "/menu")
async def menu_command(message: Message):
    """Обработчик команды /menu для отображения списка команд."""
    await message.answer(
    "📋 Выберите команду:",
    reply_markup=get_commands_menu_keyboard()
)

# --------------------- ПОКАЗ АНКЕТ ---------------------
async def show_user_profile(
    message: Union[Message, CallbackQuery],
    state: FSMContext,
    index: int
):
    data = await state.get_data()
    users = data.get("search_users", [])
    if not users or index < 0 or index >= len(users):
        if isinstance(message, CallbackQuery):
            await message.message.edit_text("Анкеты закончились. Попробуйте позже!")
        else:
            await message.answer("Анкеты закончились. Попробуйте позже!")
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
        # Подмена сообщения
        if user['photo_id']:
            await message.message.edit_caption(
                caption=text,
                reply_markup=keyboard
            )
        else:
            await message.message.edit_text(
                text=text,
                reply_markup=keyboard
            )
    else:
        # Просто новый ответ
        if user['photo_id']:
            await message.answer_photo(
                user['photo_id'],
                caption=text,
                reply_markup=keyboard
            )
        else:
            await message.answer(
                text,
                reply_markup=keyboard
            )

# --------------------- CALLBACK ЗАПРОСЫ ---------------------
@router.callback_query(F.data.startswith("course_"))
async def handle_course(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data_cb = callback.data
    course = data_cb.split("_")[1]
    if course == "master":
        course = "Магистратура"
    elif course == "phd":
        course = "Аспирантура"
    else:
        course = f"{course} курс"

    await state.update_data(course=course, user_id=callback.from_user.id, username=callback.from_user.username)
    await callback.message.answer("📷 Отправьте ваше фото (или напишите /skip для пропуска):")
    await state.set_state(ProfileCreation.awaiting_photo)

@router.callback_query(F.data == "confirm_profile")
async def confirm_profile(callback: CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    add_user(
        data_state["user_id"],
        data_state["username"],
        data_state.get("course"),
        data_state.get("photo_id"),
        data_state.get("skills"),
        data_state.get("tags")
    )
    await callback.message.edit_text(
    "✅ Анкета сохранена! Используйте /search для просмотра других анкет."
    )
    await state.clear()

@router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✅ Анкета сохранена! Используйте /search для просмотра других анкет.")
    await state.clear()

@router.callback_query(F.data.startswith("nav_"))
async def navigate_profiles(callback: CallbackQuery, state: FSMContext):
    action, index = callback.data.split("_")[1], int(callback.data.split("_")[2])
    new_index = index - 1 if action == "prev" else index + 1
    await state.update_data(search_index=new_index)
    await show_user_profile(callback, state, new_index)

@router.callback_query(F.data.startswith("tag_"))
async def handle_tag_selection(callback: CallbackQuery, state: FSMContext):
    tag = callback.data.split("tag_")[1]
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

@router.callback_query(F.data == "tags_confirm")
async def confirm_tags(callback: CallbackQuery, state: FSMContext):
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

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=get_confirm_keyboard()
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_confirm_keyboard()
        )

    await state.set_state(None)


@router.callback_query(F.data == "find_confirm")
async def find_confirm(callback: CallbackQuery, state: FSMContext):
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
        if callback.message.photo:
            await callback.message.edit_caption(
                caption="Никого не найдено по выбранным навыкам. Попробуйте изменить набор навыков."
            )
        else:
            await callback.message.edit_text(
                "Никого не найдено по выбранным навыкам. Попробуйте изменить набор навыков."
            )
        await state.set_state(None)
        return

    await state.update_data(search_users=users_sorted, search_index=0, my_tags=list(my_selected))
    await show_user_profile(callback, state, 0)
    await state.set_state(None)

@router.callback_query(F.data.startswith("command_"))
async def handle_command_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора команды из инлайн-клавиатуры."""
    command = callback.data.split("_")[1]
    msg = callback.message

    if command == "start":
        await state.clear()
        await msg.edit_text(
            "👋 Добро пожаловать в бот для поиска команды УрФУ!\nВыберите ваш курс обучения:",
            reply_markup=get_course_keyboard()
        )

    elif command == "help":
        await msg.edit_text(
            "📚 Команды бота:\n"
            "/start - Начать работу с ботом\n"
            "/profile - Просмотреть или отредактировать анкету\n"
            "/search - Просмотреть анкеты других пользователей\n"
            "/find - Найти пользователей по навыкам\n"
            "/delete_profile - Удалить свою анкету\n"
            "/menu - Показать меню команд\n"
            "/help - Показать эту справку"
        )

    elif command == "profile":
        user_id = callback.from_user.id
        user_data = get_user(user_id)
        if user_data:
            text = (
                f"📌 Ваша анкета:\n"
                f"👤 @{user_data['username']}\n"
                f"📚 Курс: {user_data['course']}\n"
                f"📝 Описание: {user_data['skills'] or 'Не указано'}\n"
                f"🛠 Навыки: {_format_tags(_parse_tags_str(user_data['tags']))}\n"
            )
            if user_data.get('photo_id'):
                await msg.edit_caption(caption=text, reply_markup=get_confirm_keyboard())
            else:
                await msg.edit_text(text, reply_markup=get_confirm_keyboard())
        else:
            await msg.edit_text("У вас нет анкеты. Создайте её с помощью /start.")

    elif command == "delete_profile":
        user_id = callback.from_user.id
        delete_user(user_id)
        await msg.edit_text("Ваша анкета удалена.")

    elif command == "search":
        user_id = callback.from_user.id
        me = get_user(user_id)
        my_tags = _parse_tags_str(me['tags'] if me else None)
        users = get_all_users(user_id)
        if not users:
            await msg.edit_text("Анкеты закончились. Попробуйте позже!")
            return
        users_sorted = sorted(users, key=lambda u: len(my_tags & _parse_tags_str(u['tags'])), reverse=True)
        await state.update_data(search_users=users_sorted, search_index=0, my_tags=list(my_tags))
        await show_user_profile(callback, state, 0)

    elif command == "find":
        await state.update_data(selected_tags=[])
        await msg.edit_text(
            "🧭 Выберите навыки для поиска:",
            reply_markup=get_tags_keyboard([], confirm_text="🔎 Найти", confirm_callback="find_confirm")
        )
        await state.set_state(FindUsers.awaiting_tags)


# --------------------- ФОТО + ОПИСАНИЕ + НАВЫКИ ---------------------
@router.message(ProfileCreation.awaiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)
    await message.answer("📝 Пару слов про себя и тех, кого вы ищете (до 500 символов):")
    await state.set_state(ProfileCreation.awaiting_skills)


@router.message(ProfileCreation.awaiting_photo, F.text == "/skip")
async def skip_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=None)
    await message.answer("📝 Пару слов про себя и тех, кого вы ищете (до 500 символов):")
    await state.set_state(ProfileCreation.awaiting_skills)


@router.message(ProfileCreation.awaiting_skills, F.text)
async def handle_skills(message: Message, state: FSMContext):
    skills = message.text[:500]
    await state.update_data(skills=skills, selected_tags=[])
    await message.answer(
        "🛠 Выберите навыки:",
        reply_markup=get_tags_keyboard([])
    )
    await state.set_state(ProfileCreation.awaiting_tags)


# --------------------- ОБРАБОТКА НЕОЖИДАННЫХ СООБЩЕНИЙ ---------------------
@router.message(F.text)
async def handle_unexpected_text(message: Message, state: FSMContext):
    """
    Обрабатывает любые текстовые сообщения, не соответствующие командам или состояниям.
    """
    await message.answer(
        "Пожалуйста, используйте команды из меню (/menu) или следуйте инструкциям."
    )