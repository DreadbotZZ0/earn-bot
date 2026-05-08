from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import get_user, get_referral_count
from keyboards.main import back_btn
from config import REFERRAL_REWARD

router = Router()

@router.callback_query(F.data == "referrals")
async def show_referrals(call: CallbackQuery):
    user = get_user(call.from_user.id)
    refs = get_referral_count(call.from_user.id)
    bot_info = await call.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
    earned = refs * REFERRAL_REWARD

    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"За каждого приглашённого друга: <b>{REFERRAL_REWARD}₸</b>\n\n"
        f"Приглашено: <b>{refs} чел.</b>\n"
        f"Заработано с рефералов: <b>{earned:,}₸</b>\n\n"
        f"🔗 Твоя ссылка:\n<code>{ref_link}</code>\n\n"
        f"Отправь другу — как только он зарегистрируется, получишь <b>{REFERRAL_REWARD}₸</b>"
    )
    await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")
    await call.answer()
