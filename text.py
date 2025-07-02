translations = {
    "ru": {
        "menu.title": "Меню парсера",
        "menu.start_parse": "[1] Запустить парсинг",
        "menu.change_language": "[2] Сменить язык",
        "menu.exit": "[3] Выход",
        "menu.select_option": "Выберите опцию [1-3]:",
        "menu.press_enter": "Нажмите Enter для продолжения...",
        "menu.starting_parse": "Запуск парсинга...",
        "menu.parse_completed": "Парсинг завершён:\nОбщее количество пользователей: {count}\nФайлы: {file}",
        "menu.invalid_choice": "Неверный выбор",
        "menu.goodbye": "До свидания!",
        "menu.language_changed": "Язык изменён на {language}",
        "menu.select_language": "Выберите язык",
        "menu.select_language_option": "Выберите опцию [0-2]:",
        "menu.back": "[0] Назад",
        "menu.file_created": "Создан файл {file}",
        "menu.dir_created": "Создана папка {dir}",
        "menu.account_skipped": "Аккаунт {phone} пропущен из-за ошибки: {error}",
        "menu.parsing_chat": "Парсинг чата {chat} с аккаунта {phone}",
        "menu.proxy_error": "Ошибка: {error}. Прокси необходим для парсинга.",
        "menu.enter_chats": "Введите ссылку(и) на чат(ы) через запятую (например, https://t.me/idochat):",
        "menu.enter_period": "Введите количество дней для парсинга (например, 7 для недели):",
        "menu.stop_confirm": "Парсинг будет остановлен, результаты не сохранятся. Продолжить? [y/n]"
    },
    "en": {
        "menu.title": "Parser Menu",
        "menu.start_parse": "[1] Start Parsing",
        "menu.change_language": "[2] Change Language",
        "menu.exit": "[3] Exit",
        "menu.select_option": "Select an option [1-3]:",
        "menu.press_enter": "Press Enter to continue...",
        "menu.starting_parse": "Starting parsing...",
        "menu.parse_completed": "Parsing completed:\nTotal users: {count}\nFiles: {file}",
        "menu.invalid_choice": "Invalid choice",
        "menu.goodbye": "Goodbye!",
        "menu.language_changed": "Language changed to {language}",
        "menu.select_language": "Select language",
        "menu.select_language_option": "Select option [0-2]:",
        "menu.back": "[0] Back",
        "menu.file_created": "Created file {file}",
        "menu.dir_created": "Created directory {dir}",
        "menu.account_skipped": "Account {phone} skipped due to error: {error}",
        "menu.parsing_chat": "Parsing chat {chat} with account {phone}",
        "menu.proxy_error": "Error: {error}. Proxy is required for parsing.",
        "menu.enter_chats": "Enter chat link(s) separated by commas (e.g., https://t.me/idochat):",
        "menu.enter_period": "Enter number of days for parsing (e.g., 7 for a week):",
        "menu.stop_confirm": "Parsing will be stopped, results will not be saved. Continue? [y/n]"
    }
}

def t(key, locale, **kwargs):
    return translations.get(locale, translations["en"]).get(key, key).format(**kwargs)