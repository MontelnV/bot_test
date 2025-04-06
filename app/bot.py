
import os
import json
import asyncio
import aiohttp
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Конфигурация бэкендов
SERVERS_CONFIG_FILE = "servers_api.json"

# Загрузка конфигурации серверов
def load_servers_config(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Файл конфигурации серверов не найден: {filepath}")
        return []
    except json.JSONDecodeError:
        logging.error(f"Ошибка при чтении файла конфигурации JSON: {filepath}")
        return []

SERVERS = load_servers_config(SERVERS_CONFIG_FILE)


# FSM States (Finite State Machine)
class ScriptExecution(StatesGroup):
    choosing_server = State()
    choosing_script = State()
    confirm_execution = State() #optional


# In-memory storage for user's selection
user_data = {}


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def make_request(url: str, method: str = "GET", data: dict = None):
    """Функция для выполнения HTTP-запросов к бэкенду."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Request to {url} failed with status {response.status}: {await response.text()}")
                    return None
    except aiohttp.ClientError as e:
        logging.error(f"AIOHTTP error: {e}")
        return None
    except Exception as e:
        logging.exception("Ошибка при выполнении HTTP-запроса")
        return None



@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(ScriptExecution.choosing_server)
    builder = InlineKeyboardBuilder()
    for server in SERVERS:
        builder.button(text=server['name'], callback_data=f"server:{server['name']}")
    builder.adjust(2)  # Adjust the number of buttons per row

    await message.answer(
        "Выберите сервер:",
        reply_markup=builder.as_markup()
    )



@dp.callback_query(ScriptExecution.choosing_server, F.data.startswith("server:"))
async def server_chosen(callback: types.CallbackQuery, state: FSMContext):
    server_name = callback.data.split(":")[1]
    await state.update_data(chosen_server=server_name)
    server = next((s for s in SERVERS if s['name'] == server_name), None)

    if not server:
        await callback.message.answer("Ошибка: Сервер не найден.")
        await state.clear()
        return

    url = server['base_url'] + "/list_scripts"
    response_data = await make_request(url)

    if response_data and 'scripts' in response_data:
        scripts = response_data['scripts']
        if scripts:
            builder = InlineKeyboardBuilder()
            for script in scripts:
                builder.button(text=script, callback_data=f"script:{script}")
            builder.adjust(1)
            await state.set_state(ScriptExecution.choosing_script)
            await callback.message.edit_text("Выберите скрипт:", reply_markup=builder.as_markup())
        else:
             await callback.message.answer("Нет доступных скриптов на этом сервере.")
             await state.clear()
    else:
        await callback.message.answer("Не удалось получить список скриптов.")
        await state.clear()
    await callback.answer()


@dp.callback_query(ScriptExecution.choosing_script, F.data.startswith("script:"))
async def script_chosen(callback: types.CallbackQuery, state: FSMContext):
    script_name = callback.data.split(":")[1]
    await state.update_data(chosen_script=script_name)
    data = await state.get_data()
    server_name = data.get('chosen_server')
    server = next((s for s in SERVERS if s['name'] == server_name), None)

    if not server:
        await callback.message.answer("Ошибка: Сервер не найден.")
        await state.clear()
        return

    url = server['base_url'] + "/run_script"
    payload = {'script_name': script_name}
    await callback.message.edit_text(f"Запускаю '{script_name}' на '{server_name}'...")
    response_data = await make_request(url, method="POST", data=payload)

    if response_data:
        output = response_data.get('output', '')
        error = response_data.get('error', '')
        return_code = response_data.get('return_code', -1)

        result_text = ""
        if output:
            result_text += f"Вывод:\n{output}\n"
        if error:
            result_text += f"Ошибки:\n{error}\n"
        if not output and not error:
            result_text += "Скрипт выполнен без вывода.\n"
        result_text += f"Код возврата: {return_code}"


        await callback.message.edit_text(result_text)
    else:
        await callback.message.edit_text("Не удалось выполнить скрипт.") #Edit
    await state.clear()
    await callback.answer()


@dp.message()
async def echo(message: types.Message):
    await message.reply("Неизвестная команда.  Попробуйте /start")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
