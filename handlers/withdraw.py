from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, deduct_balance, create_withdrawal, get_referral_count
from keyboards.main import back_btn, main_menu
from config import MIN_WITHDRAW, ADMIN_ID, MIN_REFS_TO_WITHDRAW, REQUIRED_CHANNEL

router = Router()

class WithdrawStates(StatesGroup):
    waiting_card = State()

@router.callback_query(F.data == "withdraw")
async def show_withdraw(call: CallbackQuery, state: FSMContext, bot: Bot):
    user = get_user(call.from_user.id)
    balance = user["balance"]
    refs = get_referral_count(call.from_user.id)

    # Шаг 1: проверка рефералов
    if refs < MIN_REFS_TO_WITHDRAW:
        need = MIN_REFS_TO_WITHDRAW - refs
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
        text = (
            f"💸 <b>Вывод средств</b>\n\n"
            f"Для вывода нужно пригласить <b>{MIN_REFS_TO_WITHDRAW} друзей</b>\n\n"
            f"👥 Приглашено: <b>{refs}/{MIN_REFS_TO_WITHDRAW}</b>\n"
            f"{'▓' * refs}{'░' * (MIN_REFS_TO_WITHDRAW - refs)} {refs}/{MIN_REFS_TO_WITHDRAW}\n\n"
            f"Осталось пригласить: <b>{need}</b>\n\n"
            f"🔗 Твоя ссылка:\n<code>{ref_link}</code>"
        )
        await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")
        await call.answer()
        return

    # Шаг 2: проверка подписки на канал
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=call.from_user.id)
        is_member = member.status not in ("left", "kicked", "banned")
    except Exception:
        is_member = False

    if not is_member:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Вступить в канал", url=f"https://t.me/+{str(REQUIRED_CHANNEL)[4:]}")],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="withdraw")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")],
        ])
        text = (
            f"💸 <b>Вывод средств</b>\n\n"
            f"✅ Рефералов: <b>{refs}/{MIN_REFS_TO_WITHDRAW}</b> — выполнено!\n\n"
            f"Последний шаг — вступи в наш канал,\n"
            f"чтобы получить вывод 💰"
        )
        await call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await call.answer()
        return

    # Шаг 3: проверка баланса
    if balance < MIN_WITHDRAW:
        need = MIN_WITHDRAW - balance
        text = (
            f"💸 <b>Вывод средств</b>\n\n"
            f"✅ Рефералов: <b>{refs}/{MIN_REFS_TO_WITHDRAW}</b>\n"
            f"✅ Канал: подписан\n\n"
            f"Твой баланс: <b>{balance:,}₸</b>\n"
            f"Минимальный вывод: <b>{MIN_WITHDRAW:,}₸</b>\n\n"
            f"❌ Нужно ещё <b>{need:,}₸</b> — приглашай друзей!"
        )
        await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")
        await call.answer()
        return

    # Всё ок — запрашиваем карту
    text = (
        f"💸 <b>Вывод средств</b>\n\n"
        f"✅ Рефералов: <b>{refs}/{MIN_REFS_TO_WITHDRAW}</b>\n"
        f"✅ Канал: подписан\n"
        f"✅ Баланс: <b>{balance:,}₸</b>\n\n"
        f"Введи номер карты для перевода:"
    )
    await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")
    await state.set_state(WithdrawStates.waiting_card)
    await call.answer()

@router.message(WithdrawStates.waiting_card)
async def process_card(message: Message, state: FSMContext):
    card = message.text.strip().replace(" ", "")
    if not card.isdigit() or len(card) < 16:
        await message.answer("❌ Неверный формат. Введи 16 цифр без пробелов:")
        return

    user = get_user(message.from_user.id)
    amount = user["balance"]

    deduct_balance(message.from_user.id, amount)
    create_withdrawal(user["id"], amount, card)

    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"💸 <b>Новая заявка на вывод</b>\n\n"
            f"👤 {message.from_user.full_name} (@{message.from_user.username or 'нет'})\n"
            f"💰 Сумма: <b>{amount:,}₸</b>\n"
            f"💳 Карта: <code>{card}</code>",
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
