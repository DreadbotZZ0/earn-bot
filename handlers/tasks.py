from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from database import get_user, get_channels, is_task_completed, complete_task, add_balance
from keyboards.main import tasks_keyboard, channel_link_keyboard, back_btn

router = Router()

@router.callback_query(F.data == "tasks")
async def show_tasks(call: CallbackQuery):
    user = get_user(call.from_user.id)
    channels = get_channels()

    if not channels:
        await call.message.edit_text(
            "📋 <b>Задания</b>\n\nПока нет доступных заданий. Загляни позже!",
            reply_markup=back_btn(), parse_mode="HTML"
        )
        await call.answer()
        return

    completed_ids = set()
    for ch in channels:
        if is_task_completed(user["id"], ch["id"]):
            completed_ids.add(ch["id"])

    done = len(completed_ids)
    total = len(channels)
    text = (
        f"📋 <b>Задания</b>\n\n"
        f"Выполнено: <b>{done}/{total}</b>\n\n"
        f"Подпишись на каналы и получи по <b>1 000₸</b> за каждый:"
    )
    await call.message.edit_text(text, reply_markup=tasks_keyboard(channels, completed_ids), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("check_task:"))
async def check_task(call: CallbackQuery):
    channel_db_id = int(call.data.split(":")[1])
    channels = get_channels()
    channel = next((c for c in channels if c["id"] == channel_db_id), None)

    if not channel:
        await call.answer("Задание не найдено", show_alert=True)
        return

    text = (
        f"📢 <b>{channel['title']}</b>\n\n"
        f"Подпишись на канал и нажми «Проверить подписку»\n"
        f"Награда: <b>{channel['reward']}₸</b>"
    )
    await call.message.edit_text(text, reply_markup=channel_link_keyboard(channel["link"], channel_db_id), parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "already_done")
async def already_done(call: CallbackQuery):
    await call.answer("✅ Ты уже выполнил это задание!", show_alert=True)

@router.callback_query(F.data.startswith("verify_task:"))
async def verify_task(call: CallbackQuery, bot: Bot):
    channel_db_id = int(call.data.split(":")[1])
    channels = get_channels()
    channel = next((c for c in channels if c["id"] == channel_db_id), None)

    if not channel:
        await call.answer("Задание не найдено", show_alert=True)
        return

    user = get_user(call.from_user.id)

    if is_task_completed(user["id"], channel_db_id):
        await call.answer("✅ Ты уже получил награду за этот канал!", show_alert=True)
        return

    # Check subscription
    try:
        member = await bot.get_chat_member(chat_id=channel["channel_id"], user_id=call.from_user.id)
        is_member = member.status not in ("left", "kicked", "banned")
    except Exception:
        await call.answer("❌ Не удалось проверить. Убедись что подписался.", show_alert=True)
        return

    if not is_member:
        await call.answer("❌ Ты ещё не подписан! Подпишись и попробуй снова.", show_alert=True)
        return

    # Reward
    complete_task(user["id"], channel_db_id)
    add_balance(call.from_user.id, channel["reward"])

    await call.answer(f"✅ +{channel['reward']}₸ зачислено на баланс!", show_alert=True)
    # Refresh tasks
    await show_tasks(call)
