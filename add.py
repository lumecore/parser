import json
import os
import asyncio
import logging
import random
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from opentele.api import API
import socks

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sessions_dir = 'sessions'
proxy_file = 'proxy.txt'

def load_proxies():
    proxies = []
    if not os.path.exists(proxy_file):
        raise FileNotFoundError(f"Файл {proxy_file} не найден. Прокси обязателен для работы.")
    with open(proxy_file, 'r') as f:
        for line in f:
            parts = line.strip().split(':')
            if len(parts) == 4:
                host, port, username, password = parts
                proxies.append((socks.SOCKS5, host, int(port), True, username, password))
    if not proxies:
        raise ValueError(f"Файл {proxy_file} пуст. Прокси обязателен для работы.")
    return proxies

async def initial_auth(phone, proxies):
    json_filename = phone
    session_file = os.path.join(sessions_dir, phone)
    api = API.TelegramDesktop.Generate(system="windows", unique_id=json_filename)
    
    proxy = random.choice(proxies)
    logger.info(f"Используется прокси: {proxy[1]}:{proxy[2]}")
    
    client = TelegramClient(
        session=session_file,
        api_id=api.api_id,
        api_hash=api.api_hash,
        device_model=api.device_model,
        system_version=api.system_version,
        app_version=api.app_version,
        lang_code=api.lang_code,
        system_lang_code=api.system_lang_code,
        proxy=proxy
    )
    client._init_request.lang_pack = api.lang_pack
    await client.connect()
    
    try:
        sent_code = await client.send_code_request(phone)
        code = input(f"Введите код для {phone}: ")
        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=sent_code.phone_code_hash)
        except SessionPasswordNeededError:
            two_fa = input(f"Введите пароль 2FA для {phone} (оставьте пустым, если не требуется): ")
            if two_fa:
                await client.sign_in(password=two_fa)
            else:
                logger.error(f"Требуется пароль 2FA для {phone}, но он не указан")
                return
        
        logger.info(f"Сессия для {phone} авторизована")
        
        json_path = os.path.join(sessions_dir, f"{phone}.json")
        auth_data = {
            "phone": phone,
            "session_file": phone,
            "app_id": api.api_id,
            "app_hash": api.api_hash,
            "device": api.device_model,
            "sdk": api.system_version,
            "app_version": api.app_version,
            "lang_pack": api.lang_pack,
            "lang_code": api.lang_code,
            "system_lang_code": api.system_lang_code,
            "twoFA": two_fa if two_fa else None
        }
        with open(json_path, 'w') as f:
            json.dump(auth_data, f, indent=4)
    except FloodWaitError as e:
        logger.error(f"Ограничение Telegram API для {phone}, требуется ожидание {e.seconds} секунд")
    except Exception as e:
        logger.error(f"Ошибка авторизации для {phone}: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()

async def main():
    proxies = load_proxies()
    
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
    
    while True:
        phone = input("Введите номер телефона (или оставьте пустым для завершения): ").strip()
        if not phone:
            break
        await initial_auth(phone, proxies)

if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.SelectorEventLoop())
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        exit(1)
    finally:
        loop.close()