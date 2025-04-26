from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import PeerChannel, PeerChat, PeerUser
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
API_ID = '22661093'  # Replace with your API ID from my.telegram.org
API_HASH = "344d2a8926320e2cf9211f0ffda9c03a"  # Corrected
BOT_TOKEN = "7685810612:AAEZLD5N7ILobZ2yQ-ZPi5TyAsGwHzkvWl8"  # Replace with your bot token from @BotFather

# Initialize the client
bot = TelegramClient('tagger_bot', API_ID, API_HASH)

started_users = set()
bot_groups = set()
admin_users = {5064542413}  # Your Telegram ID

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    started_users.add(user_id)
    await event.respond("👋 Welcome to the User Tagger Bot!\n\n"
                        "📌 Commands:\n"
                        "• /all [text] - Tag all users in the group\n"
                        "• utag [text] - Tag all users in the group\n"
                        "• /broadcast [message] - Send message to all users and groups (admin only)\n\n"
                        "Reply to a message with /all or utag to tag users while referencing that message.")

@bot.on(events.NewMessage(pattern=r'(/all|utag)(\s+.*)?'))
async def tag_all_handler(event):
    chat = await event.get_chat()

    if not isinstance(chat, (PeerChannel, PeerChat)) and not hasattr(chat, 'megagroup') and not getattr(chat, 'broadcast', False):
        await event.respond("This command can only be used in groups!")
        return

    if event.sender_id not in started_users:
        await event.respond("Please start the bot by sending /start in private chat first!")
        return

    extra_text = event.pattern_match.group(2)
    extra_text = extra_text.strip() if extra_text else ""

    try:
        participants = await bot.get_participants(chat)
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        await event.respond("Failed to get group members. Make sure I have the right permissions!")
        return

    valid_participants = [user for user in participants if not user.bot and user.id != event.sender_id]
    chunk_size = 5
    user_chunks = [valid_participants[i:i + chunk_size] for i in range(0, len(valid_participants), chunk_size)]

    if event.reply_to:
        replied_msg = await event.get_reply_message()
        reply_to_msg_id = replied_msg.id
    else:
        reply_to_msg_id = None

    if extra_text and user_chunks:
        msg = await bot.send_message(entity=chat.id, message=extra_text, reply_to=reply_to_msg_id)
        if msg:
            reply_to_msg_id = msg.id

    for chunk in user_chunks:
        tag_text = ""
        for user in chunk:
            first_name = user.first_name or "User"
            mention = f"[{first_name}](tg://user?id={user.id})"
            tag_text += f"🔹{mention}\n"

        if tag_text:
            await bot.send_message(entity=chat.id, message=tag_text, reply_to=reply_to_msg_id, parse_mode='markdown')
            await asyncio.sleep(2)

    if chat.id not in bot_groups:
        bot_groups.add(chat.id)

@bot.on(events.NewMessage(pattern=r'/broadcast(\s+.+)?'))
async def broadcast_handler(event):
    sender = await event.get_sender()

    if sender.id not in admin_users:
        await event.respond("You don't have permission to use this command!")
        return

    broadcast_text = event.pattern_match.group(1)
    if not broadcast_text:
        await event.respond("Please provide a message to broadcast!\nUsage: /broadcast [message]")
        return

    broadcast_text = broadcast_text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n\n🔄 Broadcast by Admin on {timestamp}"
    full_message = f"{broadcast_text}{footer}"

    sent_count = 0
    total_targets = len(started_users) + len(bot_groups)

    status_msg = await event.respond(f"🔄 Broadcasting message to {total_targets} targets...")

    for user_id in started_users:
        try:
            await bot.send_message(user_id, full_message)
            sent_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {e}")

    for group_id in bot_groups:
        try:
            await bot.send_message(group_id, full_message)
            sent_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to send broadcast to group {group_id}: {e}")

    await bot.edit_message(entity=status_msg.chat_id, message=status_msg.id,
                            text=f"✅ Broadcast completed! Message sent to {sent_count}/{total_targets} targets.")

@bot.on(events.ChatAction)
async def chat_action_handler(event):
    if event.user_added and bot.uid in event.user_ids:
        chat = await event.get_chat()
        bot_groups.add(chat.id)

        await event.respond("👋 Hello everyone! I'm User Tagger Bot.\n\n"
                            "To use me, first send me a /start command in private chat.\n"
                            "Then you can use /all or utag commands to tag all users in this group!")

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    bot_info = await bot.get_me()
    bot.uid = bot_info.id
    print(f"Bot @{bot_info.username} started successfully!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
    
