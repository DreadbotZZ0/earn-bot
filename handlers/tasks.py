from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from keyboards.main import back_btn
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(F.data == "tasks")
async def show_tasks(call: CallbackQuery, bot: Bot):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
    text = (
        f"📋 <b>Задания</b>\n\n"
        f"👥 <b>Приглашай друзей — получай деньги!</b>\n\n"
        f"За каждого приглашённого друга ты получаешь <b>1 000₸</b>\n\n"
        f"🔗 Твоя реферальная ссылка:\n"
        f"<code>{ref_link}</code>\n\n"
        f"Скопируй ссылку и отправь друзьям. Когда они запустят бота — "
        f"тебе автоматически зачислится 1 000₸ 💰"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться ссылкой", switch_inline_query=ref_link)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")],
    ])
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await call.answer()
