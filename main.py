import asyncio
from loguru import logger
from config import load_config
from menu import run_menu
from parser import run_parse


logger.remove()  
logger.add("parser.log", rotation="10 MB", format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")
logger.add(lambda msg: print(msg, end=""), colorize=True, format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}")

async def main():
    config = load_config()
    await run_menu(config, run_parse)

if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        loop.close()