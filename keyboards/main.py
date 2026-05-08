from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def reply_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="📋 Задания")],
            [KeyboardButton(text="💸 Вывести")],
        ],
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Выбери действие..."
    )

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
         InlineKeyboardButton(text="📋 Задания", callback_data="tasks")],
        [InlineKeyboardButton(text="💸 Вывести", callback_data="withdraw")],
    ])

def back_btn():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])

def tasks_keyboard(channels, completed_ids):
    buttons = []
    for ch in channels:
        done = ch["id"] in completed_ids
        status = "✅" if done else "🔔"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {ch['title']} (+{ch['reward']}₸)",
            callback_data=f"check_task:{ch['id']}" if not done else "already_done"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def channel_link_keyboard(channel_link, channel_db_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться", url=channel_link)],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data=f"verify_task:{channel_db_id}")],
        [InlineKeyboardButton(text="⬅️ К заданиям", callback_data="tasks")],
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Добавить канал", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="🗑 Удалить канал", callback_data="admin_del_channel")],
        [InlineKeyboardButton(text="💸 Заявки на вывод", callback_data="admin_withdrawals")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
    ])

def withdrawal_actions(wid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve:{wid}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{wid}")],
    ])
