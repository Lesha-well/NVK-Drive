from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import add_user, get_user, delete_user, get_all_users
from keyboards import get_course_keyboard, get_confirm_keyboard, get_navigation_keyboard

router = Router()

class ProfileCreation(StatesGroup):
    awaiting_photo = State()
    awaiting_skills = State()

@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в бот для поиска команды УрФУ!\nВыберите ваш курс обучения:",
        reply_markup=get_course_keyboard()
    )

@router.message(F.text == "/help")
async def help_command(message: Message):
    """Обработчик команды /help."""
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
    """Обработчик команды /search."""
    user_id = message.from_user.id
    users = get_all_users(user_id)
    if not users:
        await message.answer("Анкеты закончились. Попробуйте позже!")
        return
    await state.update_data(search_users=users, search_index=0)
    await show_user_profile(message, state, 0)

async def show_user_profile(message: Message, state: FSMContext, index: int):
    """Показ анкеты пользователя."""
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
    if user[3]:  # photo_id
        await message.answer_photo(user[3], caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@router.callback_query()
async def button_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатий на инлайн-кнопки."""
    data = callback.data
    await callback.answer()

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
        await callback.message.answer("📷 Отправьте ваше фото (или напишите /skip для пропуска):")
        await state.set_state(ProfileCreation.awaiting_photo)
        return

    if data == "confirm_profile":
        data = await state.get_data()
        user_id = data["user_id"]
        username = data["username"]
        course = data.get("course")
        photo_id = data.get("photo_id")
        skills = data.get("skills")
        add_user(user_id, username, course, photo_id, skills)
        await callback.message.answer("✅ Анкета сохранена! Используйте /search для просмотра других анкет.")
        await state.clear()
        return

    if data == "edit_profile":
        await callback.message.answer(
            "✏ Хотите изменить анкету? Выберите курс заново:",
            reply_markup=get_course_keyboard()
        )
        await state.clear()
        return

    if data.startswith("nav_"):
        action, index = data.split("_")[1], int(data.split("_")[2])
        new_index = index - 1 if action == "prev" else index + 1
        await state.update_data(search_index=new_index)
        await show_user_profile(callback.message, state, new_index)
        return

@router.message(ProfileCreation.awaiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    """Обработчик получения фото."""
    photo = message.photo[-1]  # Берем фото наивысшего качества
    await state.update_data(photo_id=photo.file_id)
    await message.answer("🛠 Введите описание ваших навыков (до 500 символов):")
    await state.set_state(ProfileCreation.awaiting_skills)

@router.message(ProfileCreation.awaiting_photo, F.text == "/skip")
async def skip_photo(message: Message, state: FSMContext):
    """Обработчик пропуска фото."""
    await state.update_data(photo_id=None)
    await message.answer("🛠 Введите описание ваших навыков (до 500 символов):")
    await state.set_state(ProfileCreation.awaiting_skills)

@router.message(ProfileCreation.awaiting_skills, F.text)
async def handle_skills(message: Message, state: FSMContext):
    """Обработчик получения навыков."""
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
        await message.answer_photo(data["photo_id"], caption=text, reply_markup=get_confirm_keyboard())
    else:
        await message.answer(text, reply_markup=get_confirm_keyboard())
    await state.set_state(None)