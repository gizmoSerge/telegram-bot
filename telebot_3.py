import asyncio
import logging
import config

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command

import asyncpg

from openai import AsyncOpenAI


bot = Bot(token=config.bot_token)
dp = Dispatcher()
ai_chat = AsyncOpenAI(api_key=config.ai_token)

async def create_db_connection():
    return await asyncpg.connect(user=config.db_user, password=config.db_pass, database=config.db_name, host=config.db_host)

@dp.message(CommandStart())
async def handle_start(message):
    await message.answer(text=f'Hello {message.from_user.full_name}\n Available commands:\n /add\n /getall\n /ai')

@dp.message(Command('add'))
async def handle_message(message):
    if len(message.text) < 6:
        await message.answer(text='Blank note')
    else:
        db_link = await create_db_connection()
        note_text = message.text
        user_id = message.from_user.id
        await db_link.execute('INSERT INTO notes(user_id, note_text) VALUES($1, $2)', user_id, note_text[5:])
        await message.reply('Note added')
        await db_link.close()

@dp.message(Command('getall'))
async def handle_message(message):
    db_link = await create_db_connection()
    user_id = message.from_user.id
    rows = await db_link.fetch('SELECT note_text FROM notes WHERE user_id = $1', user_id)
    notes = [row['note_text'] for row in rows]
    if not notes:
        await message.answer('No notations')
    else:
        await message.answer('\n'.join(notes))
        await db_link.execute('DELETE FROM notes WHERE user_id = $1', user_id)
    await db_link.close()

@dp.message(Command('ai'))
async def handle_message(message):
    if len(message.text) < 5:
        await message.answer(text='Ask a question')
    else:
        try:
            chat_completion = await ai_chat.chat.completions.create(messages=[{'role': 'user','content': message.text[4:],}], model='gpt-3.5-turbo')
            answer_text = chat_completion.choices[0].message.content
            await message.reply(answer_text)
        except Exception as ex_name:
            await message.reply(f'An error has occurred: {ex_name}')

@dp.message()
async def echo_message(message):
    await message.answer(text='Unknow command')

async def main():
    # logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())