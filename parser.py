import json
import os
import asyncio
import random
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import InputClientProxy
from telethon.network import ConnectionTcpFull
from telethon.errors import FloodWaitError, ChannelPrivateError
import socks
import keyboard
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt, IntPrompt
from text import t
from config import load_proxies
from loguru import logger

console = Console()


running = False
parse_task = None
client = None
global_user_cache = {}
stop_parsing = False


def load_auth_data(json_path):
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    return {}


async def estimate_total_messages(client, target_entity, time_threshold):
    try:
        
        message_count = 0
        async for _ in client.iter_messages(target_entity, limit=1000, offset_date=time_threshold):
            message_count += 1
        return max(message_count, 100)  
    except ChannelPrivateError as e:
        logger.warning(f"Чат недоступен: {e}")
        raise
    except Exception as e:
        logger.warning(f"Не удалось оценить общее количество сообщений: {e}")
        return 100  


async def parse_users(client, target_entity, days, config):
    global stop_parsing
    active_users = set()
    user_ids = set()
    time_threshold = datetime.now(timezone.utc) - timedelta(days=days)
    
    
    total_messages = await estimate_total_messages(client, target_entity, time_threshold)
    
    
    progress = Progress(
        TextColumn("[bold cyan]Обработано сообщений: {task.completed}/{task.total} ({task.percentage:.0f}%)[/bold cyan]"),
        BarColumn(),
        "{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console,
        transient=True
    )
    with progress:
        task = progress.add_task("", total=total_messages, completed=0)
        message_count = 0
        
        async for message in client.iter_messages(target_entity, limit=None):
            if stop_parsing:
                break
            if message.date < time_threshold:
                break
            if message.from_id and hasattr(message.from_id, 'user_id'):
                user_ids.add(message.from_id.user_id)
            message_count += 1
            progress.update(task, advance=1, completed=message_count)
        
        if stop_parsing:
            return set()
        
        
        batch_size = 50  
        for i in range(0, len(user_ids), batch_size):
            if stop_parsing:
                break
            batch_ids = list(user_ids)[i:i + batch_size]
            try:
                users = await client.get_entity(batch_ids)
                for user in users:
                    if user.username and f"@{user.username}" not in active_users:
                        active_users.add(f"@{user.username}")
                        global_user_cache[user.id] = user
                await asyncio.sleep(0.05)  
            except FloodWaitError as e:
                logger.warning(f"Флуд-лимит, ждем {e.seconds} секунд")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.warning(f"Не удалось получить данные пользователей: {e}")
    
    return active_users


async def process_session(json_file, config, target_entity, chat_link, proxies):
    global stop_parsing
    json_path = json_file
    auth_data = load_auth_data(json_path)
    if not auth_data:
        logger.error(f"Не удалось загрузить данные из {json_path}")
        console.print(f"[red]{t('menu.account_skipped', locale=config['language'], phone=json_path, error='Не удалось загрузить данные')}[/red]")
        return set(), False

    phone = auth_data.get('phone')
    if not phone:
        logger.error(f"Номер телефона отсутствует в {json_path}")
        console.print(f"[red]{t('menu.account_skipped', locale=config['language'], phone=json_path, error='Номер телефона отсутствует')}[/red]")
        return set(), False
    
    session_file = os.path.join(config['accounts_dir'], auth_data.get('session_file', phone))
    
    api_id = auth_data.get('app_id')
    api_hash = auth_data.get('app_hash')
    lang_pack = auth_data.get('lang_pack', 'tdesktop')
    lang_code = auth_data.get('lang_code', 'en')
    system_lang_code = auth_data.get('system_lang_code', 'en-US')
    device = auth_data.get('device', 'Desktop')
    sdk = auth_data.get('sdk', 'Windows 10')
    app_version = auth_data.get('app_version', '3.4.3 x64')

    if not all([api_id, api_hash]):
        logger.error(f"Недостаточно данных в {json_path}")
        console.print(f"[red]{t('menu.account_skipped', locale=config['language'], phone=phone, error='Недостаточно данных API')}[/red]")
        return set(), False

    if not isinstance(lang_pack, str):
        lang_pack = "tdesktop"
    if not isinstance(lang_code, str):
        lang_code = "en"
    if not isinstance(system_lang_code, str):
        system_lang_code = "en-US"

    if not os.path.exists(session_file + '.session'):
        logger.error(f"Сессия для {phone} не найдена")
        console.print(f"[red]{t('menu.account_skipped', locale=config['language'], phone=phone, error='Сессия не найдена')}[/red]")
        return set(), False

    proxy = random.choice(proxies)
    logger.info(f"Используется прокси: {proxy[1]}:{proxy[2]}")
    
    client = TelegramClient(
        session=session_file,
        api_id=api_id,
        api_hash=api_hash,
        connection=ConnectionTcpFull,
        device_model=device,
        system_version=sdk,
        app_version=app_version,
        lang_code=lang_code,
        system_lang_code=system_lang_code,
        proxy=proxy
    )
    client._init_request.lang_pack = lang_pack

    try:
        await client.connect()
        is_authorized = await client.is_user_authorized()
        if not is_authorized:
            logger.warning(f"Сессия для {phone} НЕ авторизована")
            console.print(f"[red]{t('menu.account_skipped', locale=config['language'], phone=phone, error='Сессия не авторизована')}[/red]")
            return set(), False

        logger.info(f"Сессия для {phone} авторизована")
        console.print(f"[cyan]{t('menu.parsing_chat', locale=config['language'], chat=chat_link, phone=phone)}[/cyan]")
        users = await parse_users(client, target_entity, config['days'], config)
        return users, True
    except ChannelPrivateError:
        error_msg = f"Для аккаунта {phone} чат {chat_link} недоступен"
        logger.error(error_msg)
        console.print(f"[red]{error_msg}[/red]")
        return set(), False
    except Exception as e:
        logger.error(f"Ошибка при обработке сессии для {phone}: {e}")
        console.print(f"[red]{t('menu.account_skipped', locale=config['language'], phone=phone, error=str(e))}[/red]")
        return set(), False
    finally:
        if client.is_connected():
            await client.disconnect()


async def monitor_spacebar():
    global stop_parsing
    while running:
        if keyboard.is_pressed('space'):
            response = Prompt.ask(f"[yellow]{t('menu.stop_confirm', locale='ru')}[/yellow]")
            if response.lower() == 'y':
                stop_parsing = True
                logger.info("Парсинг остановлен пользователем")
                console.print("[red]Парсинг остановлен[/red]")
            else:
                logger.info("Парсинг продолжен после запроса остановки")
        await asyncio.sleep(0.1)


async def run_parse(config):
    global running, parse_task, stop_parsing
    if running:
        console.print(f"[yellow]{t('menu.running', locale=config['language'])}[/yellow]")
        return
    running = True
    stop_parsing = False
    console.print(f"[green]{t('menu.starting_parse', locale=config['language'])}[/green]")
    
    
    chat_links = Prompt.ask(f"[cyan]{t('menu.enter_chats', locale=config['language'])}[/cyan]").split(',')
    chat_links = [link.strip() for link in chat_links if link.strip()]
    if not chat_links:
        console.print(f"[red]Не указаны ссылки на чаты[/red]")
        running = False
        return
    
    
    days = IntPrompt.ask(f"[cyan]{t('menu.enter_period', locale=config['language'])}[/cyan]", default=7)
    config['days'] = max(1, days)  
    
    try:
        
        if not os.path.exists(config['accounts_dir']):
            os.makedirs(config['accounts_dir'])
            console.print(f"[green]{t('menu.dir_created', locale=config['language'], dir=config['accounts_dir'])}[/green]")
            logger.info(f"Создана папка {config['accounts_dir']}")

        
        if not os.path.exists('users'):
            os.makedirs('users')
            console.print(f"[green]{t('menu.dir_created', locale=config['language'], dir='users')}[/green]")
            logger.info("Создана папка users")

        
        try:
            proxies = load_proxies(config['proxy_file'], config)
        except Exception as e:
            console.print(f"[red]{t('menu.proxy_error', locale=config['language'], error=str(e))}[/red]")
            running = False
            return

        json_files = [f for f in os.listdir(config['accounts_dir']) if f.endswith('.json')]
        if not json_files:
            logger.error(f"Не найдено JSON-файлов в {config['accounts_dir']}")
            console.print(f"[red]Не найдено JSON-файлов в {config['accounts_dir']}[/red]")
            running = False
            return

        
        first_json = os.path.join(config['accounts_dir'], json_files[0])
        auth_data = load_auth_data(first_json)
        session_file = os.path.join(config['accounts_dir'], auth_data.get('session_file', auth_data.get('phone')))
        client = TelegramClient(
            session=session_file,
            api_id=auth_data.get('app_id'),
            api_hash=auth_data.get('app_hash'),
            proxy=random.choice(proxies)
        )
        target_entities = []
        try:
            await client.connect()
            for chat_link in chat_links:
                try:
                    entity = await client.get_entity(chat_link)
                    target_entities.append((chat_link, entity))
                except Exception as e:
                    logger.error(f"Не удалось получить сущность чата {chat_link}: {e}")
                    console.print(f"[red]Не удалось получить сущность чата {chat_link}: {e}[/red]")
            await client.disconnect()
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            console.print(f"[red]Ошибка подключения: {e}[/red]")
            running = False
            return
        if not target_entities:
            console.print(f"[red]Не удалось получить ни одну сущность чата[/red]")
            running = False
            return

        
        spacebar_task = asyncio.create_task(monitor_spacebar())
        
        
        chat_users = {chat_link: set() for chat_link, _ in target_entities}
        
        for chat_link, target_entity in target_entities:
            if stop_parsing:
                break
            for json_file in json_files:
                if stop_parsing:
                    break
                json_path = os.path.join(config['accounts_dir'], json_file)
                users, success = await process_session(json_path, config, target_entity, chat_link, proxies)
                if success:
                    chat_users[chat_link].update(users)
                await asyncio.sleep(2)  

        
        spacebar_task.cancel()
        
        if stop_parsing:
            console.print(f"[red]Парсинг прерван, результаты не сохранены[/red]")
            running = False
            return

        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=config['days'])
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        
        files_created = []
        for chat_link, users in chat_users.items():
            chat_name = chat_link.split('/')[-1].replace('@', '')
            count = len(users)
            filename = f"{chat_name}_{config['days']}days_{start_date_str}_{end_date_str}_{count}.txt"
            output_path = os.path.join('users', filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Формат: @username\n")
                for user in users:
                    f.write(f"{user}\n")
            console.print(f"[green]{t('menu.file_created', locale=config['language'], file=output_path)}[/green]")
            files_created.append(output_path)

        
        all_users = set().union(*chat_users.values())
        total_count = len(all_users)
        
        
        report = f"{t('menu.parse_completed', locale=config['language'], count=total_count, file=', '.join(files_created))}\n"
        for chat_link, users in chat_users.items():
            report += f"- {chat_link}: {len(users)} пользователей\n"
        console.print(Panel(report, style="bold cyan"))
        
    except Exception as e:
        console.print(Panel(f"Ошибка: {e}", style="bold red"))
    finally:
        running = False
        stop_parsing = False