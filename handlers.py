from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import add_user, get_user, delete_user, get_all_users
from keyboards import get_course_keyboard, get_confirm_keyboard, get_navigation_keyboard
from utils import send_message_and_delete_command, replace_message

router = Router()

class ProfileCreation(StatesGroup):
    awaiting_photo = State()
    awaiting_skills = State()


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
            f"👤 @{user_data[1]}\n"
            f"📚 Курс: {user_data[2]}\n"
            f"🛠 Навыки: {user_data[4] or 'Не указаны'}\n"
        )
        if user_data[3]:  # photo_id
            await send_message_and_delete_command(message, text, keyboard=get_confirm_keyboard(), photo_id=user_data[3])
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
    users = get_all_users(user_id)
    if not users:
        await send_message_and_delete_command(message, "Анкеты закончились. Попробуйте позже!")
        return

    await state.update_data(search_users=users, search_index=0)
    await show_user_profile(message, state, 0)
# ----------------------------------------------------


# --------------------- ПОКАЗ АНКЕТ ---------------------
async def show_user_profile(message: Message | CallbackQuery, state: FSMContext, index: int):
    data = await state.get_data()
    users = data.get("search_users", [])
    if not users or index < 0 or index >= len(users):
        await message.answer("Анкеты закончились. Попробуйте позже!")
        return

    user = users[index]
    text = (
        f"👤 @{user[1]}\n"
        f"📚 Курс: {user[2]}\n"
        f"🛠 Навыки: {user[4] or 'Не указаны'}\n"
    )
    keyboard = get_navigation_keyboard(index, len(users))

    if isinstance(message, CallbackQuery):
        await replace_message(message.bot, message, new_text=text, keyboard=keyboard, photo_id=user[3] if user[3] else None)
    else:
        if user[3]:
            await send_message_and_delete_command(message, text, keyboard=keyboard, photo_id=user[3])
        else:
            await send_message_and_delete_command(message, text, keyboard=keyboard)
# ----------------------------------------------------


# --------------------- CALLBACK ---------------------
@router.callback_query()
async def button_callback(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    await callback.answer()

    # Выбор курса
    if data.startswith("course_"):
        course = {
            "course_1": "1 курс",
            "course_2": "2 курс",
            "course_3": "3 курс",
            "course_4": "4 курс",
            "course_master": "Магистратура",
            "course_phd": "Аспирантура",
        }[data]

        await state.update_data(course=course, user_id=callback.from_user.id, username=callback.from_user.username)

        await replace_message(
            bot=callback.bot,
            callback=callback,
            new_text="📷 Отправьте ваше фото (или напишите /skip для пропуска):"
        )
        await state.set_state(ProfileCreation.awaiting_photo)
        return

    # Подтверждение анкеты
    if data == "confirm_profile":
        data_state = await state.get_data()
        add_user(
            data_state["user_id"],
            data_state["username"],
            data_state.get("course"),
            data_state.get("photo_id"),
            data_state.get("skills")
        )
        await replace_message(callback.bot, callback, "✅ Анкета сохранена! Используйте /search для просмотра других анкет.")
        await state.clear()
        return

    # Редактирование анкеты
    if data == "edit_profile":
        await replace_message(
            bot=callback.bot,
            callback=callback,
            new_text="✏ Хотите изменить анкету? Выберите курс заново:",
            keyboard=get_course_keyboard()
        )
        await state.clear()
        return

    # Навигация по анкетам
    if data.startswith("nav_"):
        action, index = data.split("_")[1], int(data.split("_")[2])
        new_index = index - 1 if action == "prev" else index + 1
        await state.update_data(search_index=new_index)
        await show_user_profile(callback, state, new_index)
        return
# ----------------------------------------------------


# --------------------- ФОТО + НАВЫКИ ---------------------
@router.message(ProfileCreation.awaiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)
    await send_message_and_delete_command(message, "🛠 Введите описание ваших навыков (до 500 символов):")
    await state.set_state(ProfileCreation.awaiting_skills)


@router.message(ProfileCreation.awaiting_photo, F.text == "/skip")
async def skip_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=None)
    await send_message_and_delete_command(message, "🛠 Введите описание ваших навыков (до 500 символов):")
    await state.set_state(ProfileCreation.awaiting_skills)


@router.message(ProfileCreation.awaiting_skills, F.text)
async def handle_skills(message: Message, state: FSMContext):
    skills = message.text[:500]
    await state.update_data(skills=skills)
    data = await state.get_data()
    text = (
        f"📌 Ваша анкета:\n"
        f"👤 @{data['username']}\n"
        f"📚 Курс: {data['course']}\n"
        f"🛠 Навыки: {skills}\n"
    )

    if data.get("photo_id"):
        await send_message_and_delete_command(message, text, keyboard=get_confirm_keyboard(), photo_id=data["photo_id"])
    else:
        await send_message_and_delete_command(message, text, keyboard=get_confirm_keyboard())

    await state.set_state(None)
# ----------------------------------------------------
