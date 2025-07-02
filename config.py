import json
import os
import socks
from loguru import logger

CONFIG_FILE = 'config.json'
PROXY_FILE = 'proxy.txt'

def load_config():
    default_config = {
        'accounts_dir': 'sessions',
        'proxy_file': 'proxy.txt',
        'language': 'ru'
    }
    if not os.path.exists(CONFIG_FILE):
        logger.info(f"Файл {CONFIG_FILE} не найден, создаётся с настройками по умолчанию")
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        default_config.update(config)
    return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_proxies(proxy_file, config):
    proxies = []
    if not os.path.exists(proxy_file):
        logger.info(f"Файл {proxy_file} не найден, создаётся пустой файл")
        with open(proxy_file, 'w') as f:
            f.write("# Формат: host:port:username:password\n")
        logger.error(f"Файл {proxy_file} отсутствует, прокси необходим для парсинга")
        raise FileNotFoundError(f"Файл {proxy_file} не найден")
    with open(proxy_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                parts = line.strip().split(':')
                if len(parts) == 4:
                    host, port, username, password = parts
                    proxies.append((socks.SOCKS5, host, int(port), True, username, password))
                else:
                    logger.warning(f"Некорректный формат строки в {proxy_file}: {line.strip()}")
    if not proxies:
        logger.error(f"Файл {proxy_file} пуст, прокси необходим для парсинга")
        raise ValueError(f"Файл {proxy_file} пуст")
    return proxies