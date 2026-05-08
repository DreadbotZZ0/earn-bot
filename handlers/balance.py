from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import get_user, get_referral_count
from keyboards.main import back_btn

router = Router()

@router.callback_query(F.data == "balance")
async def show_balance(call: CallbackQuery):
    from config import MIN_WITHDRAW
    user = get_user(call.from_user.id)
    refs = get_referral_count(call.from_user.id)
    text = (
        f"💰 <b>Твой баланс</b>\n\n"
        f"На счёте: <b>{user['balance']:,}₸</b>\n\n"
        f"👥 Приглашено друзей: <b>{refs}</b>\n\n"
        f"💸 Минимальный вывод: <b>{MIN_WITHDRAW:,}₸</b>"
    )
    await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")
    await call.answer()
