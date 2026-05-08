from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (get_channels, add_channel, delete_channel,
                      get_pending_withdrawals, get_withdrawal,
                      update_withdrawal, add_balance, get_stats, get_all_users)
from keyboards.main import admin_menu, withdrawal_actions, back_btn
from config import ADMIN_ID

router = Router()

class AdminStates(StatesGroup):
    add_channel_id = State()
    add_channel_title = State()
    add_channel_link = State()

def is_admin(user_id):
    return user_id == ADMIN_ID

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("👑 <b>Панель администратора</b>", reply_markup=admin_menu(), parse_mode="HTML")

@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    users, total_paid, pending = get_stats()
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"💸 Выплачено: <b>{total_paid:,}₸</b>\n"
        f"⏳ Заявок ожидает: <b>{pending}</b>"
    )
    await call.message.edit_text(text, reply_markup=admin_menu(), parse_mode="HTML")
    await call.answer()

# --- Add channel ---
@router.callback_query(F.data == "admin_add_channel")
async def admin_add_channel(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "📢 Введи <b>ID канала</b> (например: @mychannel или -1001234567890):",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_channel_id)
    await call.answer()

@router.message(AdminStates.add_channel_id)
async def process_channel_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(channel_id=message.text.strip())
    await message.answer("✏️ Введи <b>название</b> канала:", parse_mode="HTML")
    await state.set_state(AdminStates.add_channel_title)

@router.message(AdminStates.add_channel_title)
async def process_channel_title(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(title=message.text.strip())
    await message.answer("🔗 Введи <b>ссылку</b> на канал (https://t.me/...):", parse_mode="HTML")
    await state.set_state(AdminStates.add_channel_link)

@router.message(AdminStates.add_channel_link)
async def process_channel_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    ok = add_channel(data["channel_id"], data["title"], message.text.strip())
    await state.clear()
    if ok:
        await message.answer(f"✅ Канал <b>{data['title']}</b> добавлен!", reply_markup=admin_menu(), parse_mode="HTML")
    else:
        await message.answer("❌ Канал уже существует.", reply_markup=admin_menu())

# --- Delete channel ---
@router.callback_query(F.data == "admin_del_channel")
async def admin_del_channel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    channels = get_channels()
    if not channels:
        await call.message.edit_text("📭 Нет каналов для удаления.", reply_markup=admin_menu())
        await call.answer()
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [[InlineKeyboardButton(text=f"🗑 {ch['title']}", callback_data=f"del_ch:{ch['id']}")]
               for ch in channels]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")])
    await call.message.edit_text(
        "🗑 <b>Выбери канал для удаления:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("del_ch:"))
async def confirm_del_channel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = int(call.data.split(":")[1])
    delete_channel(ch_id)
    await call.answer("✅ Канал удалён", show_alert=True)
    # Refresh list
    channels = get_channels()
    if not channels:
        await call.message.edit_text("📭 Каналов больше нет.", reply_markup=admin_menu())
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [[InlineKeyboardButton(text=f"🗑 {ch['title']}", callback_data=f"del_ch:{ch['id']}")]
               for ch in channels]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_admin")])
    await call.message.edit_text(
        "🗑 <b>Выбери канал для удаления:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_admin")
async def back_admin(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text("👑 <b>Панель администратора</b>", reply_markup=admin_menu(), parse_mode="HTML")
    await call.answer()

# --- Withdrawals ---
@router.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = get_pending_withdrawals()
    if not rows:
        await call.message.edit_text("✅ Нет заявок на вывод.", reply_markup=admin_menu())
        await call.answer()
        return

    for row in rows:
        name = row["full_name"] or row["username"] or str(row["tg_id"])
        text = (
            f"💸 <b>Заявка #{row['id']}</b>\n\n"
            f"👤 {name}\n"
            f"💰 Сумма: <b>{row['amount']:,}₸</b>\n"
            f"💳 Карта: <code>{row['card_number']}</code>\n"
            f"📅 {row['created_at']}"
        )
        await call.message.answer(text, reply_markup=withdrawal_actions(row["id"]), parse_mode="HTML")

    await call.answer()

@router.callback_query(F.data.startswith("approve:"))
async def approve_withdrawal(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    wid = int(call.data.split(":")[1])
    row = get_withdrawal(wid)
    if not row or row["status"] != "pending":
        await call.answer("Заявка уже обработана", show_alert=True)
        return
    update_withdrawal(wid, "approved")
    try:
        await call.bot.send_message(
            row["tg_id"],
            f"✅ <b>Выплата одобрена!</b>\n\n"
            f"Сумма <b>{row['amount']:,}₸</b> переведена на карту.\n"
            f"Спасибо за использование сервиса! 🎉",
            parse_mode="HTML"
        )
    except Exception:
        pass
    await call.message.edit_text(f"✅ Заявка #{wid} одобрена и выплачена.")
    await call.answer()

@router.callback_query(F.data.startswith("reject:"))
async def reject_withdrawal(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    wid = int(call.data.split(":")[1])
    row = get_withdrawal(wid)
    if not row or row["status"] != "pending":
        await call.answer("Заявка уже обработана", show_alert=True)
        return
    update_withdrawal(wid, "rejected")
    # Return money
    add_balance(row["tg_id"], row["amount"])
    try:
        await call.bot.send_message(
            row["tg_id"],
            f"❌ <b>Заявка отклонена.</b>\n\n"
            f"Сумма <b>{row['amount']:,}₸</b> возвращена на баланс.",
            parse_mode="HTML"
        )
    except Exception:
        pass
    await call.message.edit_text(f"❌ Заявка #{wid} отклонена, деньги возвращены.")
    await call.answer()

# Broadcast
@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("Использование: /broadcast Текст сообщения")
        return
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass
    await message.answer(f"✅ Отправлено {sent} из {len(users)} пользователей.")
