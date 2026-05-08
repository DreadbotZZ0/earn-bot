from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from database import get_user, create_user, add_balance, get_referral_count
from keyboards.main import main_menu
from config import REFERRAL_REWARD

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split()
    referrer_id = None

    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id == message.from_user.id:
                referrer_id = None
        except ValueError:
            referrer_id = None

    user = get_user(message.from_user.id)
    is_new = user is None

    if is_new:
        create_user(
            tg_id=message.from_user.id,
            username=message.from_user.username or "",
            full_name=message.from_user.full_name or "",
            referrer_id=referrer_id
        )
        # Reward referrer
        if referrer_id:
            ref_user = get_user(referrer_id)
            if ref_user:
                add_balance(referrer_id, REFERRAL_REWARD)
                try:
                    await message.bot.send_message(
                        referrer_id,
                        f"🎉 По твоей ссылке зарегистрировался новый пользователь!\n"
                        f"💰 +{REFERRAL_REWARD}₸ на баланс"
                    )
                except Exception:
                    pass

    text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Зарабатывай деньги за:\n"
        "👥 Приглашение друзей — <b>1 000₸</b> за каждого\n\n"
        "Выбери действие:"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")

@router.callback_query(F.data == "main_menu")
async def go_main_menu(call: CallbackQuery):
    text = (
        "👋 <b>Главное меню</b>\n\n"
        "👥 Приглашение друга — <b>1 000₸</b>\n"
        "💸 Минимальный вывод: <b>5 000₸</b>\n\n"
        "Выбери действие:"
    )
    await call.message.edit_text(text, reply_markup=main_menu(), parse_mode="HTML")
    await call.answer()
