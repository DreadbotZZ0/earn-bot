import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CHANNEL_REWARD = 1000       # ₸ за подписку на канал
REFERRAL_REWARD = 500       # ₸ за приглашённого друга
MIN_WITHDRAW = 10000        # ₸ минимальная сумма вывода
MIN_REFS_TO_WITHDRAW = 10   # минимум рефералов для вывода
REQUIRED_CHANNEL = -1003016144515  # закрытый канал — подписка нужна для вывода
