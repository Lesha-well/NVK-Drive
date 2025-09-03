# Хелперы для замены/отправки сообщений
from aiogram import Bot
from aiogram.types import Message, CallbackQuery

async def send_message_and_delete_command(message: Message, new_text: str, keyboard=None, photo_id: str | None = None):
    """
    Удаляет сообщение пользователя (например, команду /start)
    и отправляет новое сообщение от бота.
    """
    try:
        await message.delete()
    except:
        pass  # если бот не имеет прав удалять сообщение

    if photo_id:
        await message.bot.send_photo(message.chat.id, photo=photo_id, caption=new_text, reply_markup=keyboard)
    else:
        await message.bot.send_message(message.chat.id, new_text, reply_markup=keyboard)


async def replace_message(bot: Bot, callback: CallbackQuery, new_text: str, keyboard=None, photo_id: str | None = None):
    """
    Удаляет сообщение с кнопками и отправляет новое.
    """
    await callback.message.delete()

    if photo_id:
        await bot.send_photo(callback.from_user.id, photo=photo_id, caption=new_text, reply_markup=keyboard)
    else:
        await bot.send_message(callback.from_user.id, new_text, reply_markup=keyboard)

    await callback.answer()