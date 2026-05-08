from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import get_user, create_user, add_balance, get_referral_count
from keyboards.main import main_menu, reply_menu, back_btn
from config import REFERRAL_REWARD, MIN_WITHDRAW

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
        f"👥 Приглашение друзей — <b>{REFERRAL_REWARD:,}₸</b> за каждого\n\n"
        "Выбери действие:"
    )
    await message.answer(text, reply_markup=reply_menu(), parse_mode="HTML")

@router.callback_query(F.data == "main_menu")
async def go_main_menu(call: CallbackQuery):
    text = (
        "👋 <b>Главное меню</b>\n\n"
        f"👥 Приглашение друга — <b>{REFERRAL_REWARD:,}₸</b>\n"
        f"💸 Минимальный вывод: <b>{MIN_WITHDRAW:,}₸</b>\n\n"
        "Выбери действие:"
    )
    await call.message.edit_text(text, reply_markup=main_menu(), parse_mode="HTML")
    await call.answer()

# --- Reply keyboard text handlers ---

@router.message(F.text == "💰 Баланс")
async def text_balance(message: Message):
    user = get_user(message.from_user.id)
    refs = get_referral_count(message.from_user.id)
    text = (
        f"💰 <b>Твой баланс</b>\n\n"
        f"На счёте: <b>{user['balance']:,}₸</b>\n\n"
        f"👥 Приглашено друзей: <b>{refs}</b>\n\n"
        f"💸 Минимальный вывод: <b>{MIN_WITHDRAW:,}₸</b>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📋 Задания")
async def text_tasks(message: Message, bot: Bot):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться ссылкой", switch_inline_query=ref_link)],
    ])
    text = (
        f"📋 <b>Задания</b>\n\n"
        f"👥 <b>Приглашай друзей — получай деньги!</b>\n\n"
        f"За каждого приглашённого друга ты получаешь <b>{REFERRAL_REWARD:,}₸</b>\n\n"
        f"🔗 Твоя реферальная ссылка:\n"
        f"<code>{ref_link}</code>\n\n"
        f"Скопируй и отправь друзьям — получишь {REFERRAL_REWARD:,}₸ автоматически 💰"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text == "💸 Вывести")
async def text_withdraw(message: Message, state: FSMContext, bot: Bot):
    from config import REQUIRED_CHANNEL, REQUIRED_CHANNEL_LINK
    from handlers.withdraw import WithdrawStates
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    user = get_user(message.from_user.id)
    balance = user["balance"]

    if balance < MIN_WITHDRAW:
        need = MIN_WITHDRAW - balance
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
        text = (
            f"💸 <b>Вывод средств</b>\n\n"
            f"Твой баланс: <b>{balance:,}₸</b>\n"
            f"Минимальный вывод: <b>{MIN_WITHDRAW:,}₸</b>\n\n"
            f"❌ Нужно ещё <b>{need:,}₸</b>\n\n"
            f"Приглашай друзей и получай <b>{REFERRAL_REWARD:,}₸</b> за каждого:\n"
            f"<code>{ref_link}</code>"
        )
        await message.answer(text, parse_mode="HTML")
        return

    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=message.from_user.id)
        is_member = member.status not in ("left", "kicked", "banned")
    except Exception:
        is_member = False

    if not is_member:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Вступить в канал", url=REQUIRED_CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Я подписался — продолжить", callback_data="withdraw")],
        ])
        text = (
            f"💸 <b>Вывод средств</b>\n\n"
            f"✅ Баланс: <b>{balance:,}₸</b> — достаточно!\n\n"
            f"Последний шаг — вступи в наш канал,\n"
            f"чтобы получить вывод 💰"
        )
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        return

    text = (
        f"💸 <b>Вывод средств</b>\n\n"
        f"✅ Баланс: <b>{balance:,}₸</b>\n"
        f"✅ Канал: подписан\n\n"
        f"Введи номер карты для перевода:"
    )
    await message.answer(text, parse_mode="HTML")
    await state.set_state(WithdrawStates.waiting_card)
