import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_REWARD = 1000       # ₸ за подписку на канал
REFERRAL_REWARD = 1000      # ₸ за приглашённого друга
MIN_WITHDRAW = 5000         # ₸ минимальная сумма вывода
REQUIRED_CHANNEL = -1003016144515        # ID закрытого канала
REQUIRED_CHANNEL_LINK = "https://t.me/+FRcfmjrZJiAzNmJi"  # ссылка на канал
