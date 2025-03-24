import asyncio
import os
import subprocess
import logging
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command, CommandObject
from aiogram import Bot, Dispatcher, types

from dotenv import load_dotenv

load_dotenv()

SCRIPTS_DIRECTORY = os.getenv("SCRIPTS_DIRECTORY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(F.text, Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для запуска bash-скриптов.\nДоступные команды: /list, /run <имя_скрипта>")

@dp.message(F.text, Command("list"))
async def list_scripts(message: types.Message):
    try:
        scripts = [f for f in os.listdir(SCRIPTS_DIRECTORY) if os.path.isfile(os.path.join(SCRIPTS_DIRECTORY, f)) and f.endswith('.sh')]
        if scripts:
            script_list = "\n".join(scripts)
            await message.reply(f"Доступные скрипты:\n{script_list}")
        else:
            await message.reply("В директории нет доступных скриптов.")
    except Exception as e:
        logging.exception("Ошибка при получении списка скриптов")
        await message.reply(f"Ошибка при получении списка скриптов: {e}")


@dp.message(F.text, Command("run"))
async def run_script(message: types.Message, command: CommandObject):
    try:
        args = command.args
        print(args)
        if not args:
            await message.reply("Пожалуйста, укажите имя скрипта для запуска.")
            return

        script_name = args
        script_path = os.path.join(SCRIPTS_DIRECTORY, script_name)

        if not os.path.exists(script_path):
            await message.reply(f"Скрипт '{script_name}' не найден.")
            return

        os.chmod(script_path, 0o755)
        await message.reply(f"Запускаю скрипт '{script_name}'...")

        process = await asyncio.create_subprocess_exec(
            'bash', script_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        output = stdout.decode('utf-8', errors='ignore')
        error = stderr.decode('utf-8', errors='ignore')

        if output:
            await message.reply(f"Вывод скрипта:\n{output}")
        if error:
            await message.reply(f"Ошибки скрипта:\n{error}")
        if not output and not error:
            await message.reply("Скрипт выполнен, но не выдал никакого вывода.")

    except Exception as e:
        logging.exception("Ошибка при выполнении скрипта")
        await message.reply(f"Ошибка при выполнении скрипта: {e}")

@dp.message()
async def echo(message: types.Message):
    await message.reply("Неизвестная команда.  Попробуйте /start")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
