import asyncio


PERSIAN_MONTHS = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}


async def is_user_member(bot, user_id, chat_id):
    try:
        member = await bot.get_chat_member(
            chat_id=f"@{chat_id}",
            user_id=user_id
        )
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False