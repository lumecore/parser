import json
import os
import asyncio
import logging
import random
import uuid
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from opentele.api import API
import socks
import qrcode
import time

# Настройка логирования
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
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


def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=1, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)
    print("Отсканируйте QR-код в приложении Telegram.")


async def initial_auth(session_id, proxies):
    json_filename = session_id
    session_file = os.path.join(sessions_dir, session_id)
    api = API.TelegramDesktop.Generate(system="windows", unique_id=json_filename)
    
    proxy = random.choice(proxies)
    
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
        
        qr_login = await client.qr_login()
        qr_url = qr_login.url
        
        
        start_time = time.time()
        while time.time() - start_time < 60:
            os.system('cls' if os.name == 'nt' else 'clear')
            generate_qr_code(qr_url)
            try:
                await qr_login.wait(1)
                break
            except SessionPasswordNeededError:
                two_fa = input(f"Введите пароль 2FA для сессии {session_id}: ")
                if two_fa:
                    await client.sign_in(password=two_fa)
                else:
                    logger.error(f"Требуется пароль 2FA для сессии {session_id}, но он не указан")
                    return
            except asyncio.TimeoutError:
                if time.time() - start_time > 30:
                    start_time = time.time()
        
        
        if await client.is_user_authorized():
            user = await client.get_me()
            phone = user.phone if user.phone else "unknown"
            logger.info(f"Сессия {session_id} авторизована для номера {phone}")
            
            
            json_path = os.path.join(sessions_dir, f"{session_id}.json")
            auth_data = {
                "session_id": session_id,
                "phone": phone,
                "session_file": session_id,
                "app_id": api.api_id,
                "app_hash": api.api_hash,
                "device": api.device_model,
                "sdk": api.system_version,
                "app_version": api.app_version,
                "lang_pack": api.lang_pack,
                "lang_code": api.lang_code,
                "system_lang_code": api.system_lang_code,
                "twoFA": two_fa if 'two_fa' in locals() else None
            }
            with open(json_path, 'w') as f:
                json.dump(auth_data, f, indent=4)
        else:
            logger.error(f"Авторизация не удалась для сессии {session_id}")
    except FloodWaitError as e:
        logger.error(f"Ограничение Telegram API для сессии {session_id}, ожидание {e.seconds} секунд")
    except Exception as e:
        logger.error(f"Ошибка авторизации для сессии {session_id}: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()


async def main():
    proxies = load_proxies()
    
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)
    
    session_id = str(uuid.uuid4())
    await initial_auth(session_id, proxies)

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