from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from typing import Union, Optional

async def send_message(
    message: Message,
    new_text: str,
    keyboard=None,
    photo_id: Union[str, None] = None,
    reply_markup=None
):
    """
    Удаляет сообщение пользователя и отправляет новое сообщение от бота.
    """
    try:
        await message.delete()
    except:
        pass  # Если бот не имеет прав удалять сообщение

    if photo_id:
        await message.bot.send_photo(
            message.chat.id,
            photo=photo_id,
            caption=new_text,
            reply_markup=keyboard if keyboard else reply_markup
        )
    else:
        await message.bot.send_message(
            message.chat.id,
            new_text,
            reply_markup=keyboard if keyboard else reply_markup
        )

async def replace_message(
    bot: Bot,
    callback: CallbackQuery,
    new_text: str,
    keyboard=None,
    photo_id: Union[str, None] = None,
    reply_markup=None
):
    """
    Заменяет сообщение с кнопками на новое без удаления сообщения пользователя.
    """
    await callback.message.delete()

    if photo_id:
        await bot.send_photo(
            callback.from_user.id,
            photo=photo_id,
            caption=new_text,
            reply_markup=keyboard if keyboard else reply_markup
        )
    else:
        await bot.send_message(
            callback.from_user.id,
            new_text,
            reply_markup=keyboard if keyboard else reply_markup
        )

    await callback.answer()