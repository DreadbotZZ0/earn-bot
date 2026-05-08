from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user, deduct_balance, create_withdrawal
from keyboards.main import back_btn, main_menu
from config import MIN_WITHDRAW, ADMIN_ID

router = Router()

class WithdrawStates(StatesGroup):
    waiting_card = State()

@router.callback_query(F.data == "withdraw")
async def show_withdraw(call: CallbackQuery, state: FSMContext):
    user = get_user(call.from_user.id)
    balance = user["balance"]

    if balance < MIN_WITHDRAW:
        need = MIN_WITHDRAW - balance
        text = (
            f"💸 <b>Вывод средств</b>\n\n"
            f"Твой баланс: <b>{balance:,}₸</b>\n"
            f"Минимальный вывод: <b>{MIN_WITHDRAW:,}₸</b>\n\n"
            f"❌ Недостаточно средств.\n"
            f"Нужно ещё <b>{need:,}₸</b> — подпишись на каналы или пригласи друзей!"
        )
        await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")
        await call.answer()
        return

    text = (
        f"💸 <b>Вывод средств</b>\n\n"
        f"Доступно: <b>{balance:,}₸</b>\n"
        f"Минимальный вывод: <b>{MIN_WITHDRAW:,}₸</b>\n\n"
        f"Введи номер карты для перевода:"
    )
    await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")
    await state.set_state(WithdrawStates.waiting_card)
    await call.answer()

@router.message(WithdrawStates.waiting_card)
async def process_card(message: Message, state: FSMContext):
    card = message.text.strip().replace(" ", "")
    if not card.isdigit() or len(card) < 16:
        await message.answer("❌ Неверный формат карты. Введи 16 цифр без пробелов:")
        return

    user = get_user(message.from_user.id)
    amount = user["balance"]

    deduct_balance(message.from_user.id, amount)
    create_withdrawal(user["id"], amount, card)

    # Notify admin
    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"💸 <b>Новая заявка на вывод</b>\n\n"
            f"👤 {message.from_user.full_name} (@{message.from_user.username or 'нет'})\n"
            f"💰 Сумма: <b>{amount:,}₸</b>\n"
            f"💳 Карта: <code>{card}</code>\n\n"
            f"/withdrawals — посмотреть все заявки",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await state.clear()
    await message.answer(
        f"✅ <b>Заявка отправлена!</b>\n\n"
        f"Сумма: <b>{amount:,}₸</b>\n"
        f"Карта: <code>{card}</code>\n\n"
        f"Ожидай перевода в течение 24 часов.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
