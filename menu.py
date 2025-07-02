import os
import json
import asyncio
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from text import t
from loguru import logger

console = Console()


running = False


def display_menu(config, running):
    os.system("cls" if os.name == "nt" else "clear")
    console.print(f"[bold cyan]{t('menu.title', locale=config['language'])}[/bold cyan]")
    console.print(t("menu.start_parse", locale=config['language']))
    console.print(t("menu.change_language", locale=config['language']))
    console.print(t("menu.exit", locale=config['language']))
    console.print()


def change_language(config):
    logger.info("Смена языка")
    console.print(f"[bold cyan]{t('menu.select_language', locale=config['language'])}[/bold cyan]")
    console.print("[1] Русский")
    console.print("[2] English")
    console.print(f"{t('menu.back', locale=config['language'])}")
    choice = IntPrompt.ask(
        f"[cyan]{t('menu.select_language_option', locale=config['language'])}[/cyan]",
        choices=["0", "1", "2"]
    )
    if choice == 0:
        console.print(f"[yellow]{t('menu.back', locale=config['language'])}[/yellow]")
        return
    elif choice == 1:
        config['language'] = 'ru'
        console.print(f"[green]{t('menu.language_changed', locale=config['language'], language='Русский')}[/green]")
    elif choice == 2:
        config['language'] = 'en'
        console.print(f"[green]{t('menu.language_changed', locale=config['language'], language='English')}[/green]")
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)


async def run_menu(config, run_parse_func):
    global running
    running = False
    while True:
        display_menu(config, running)
        choice = Prompt.ask(
            f"[bold cyan]{t('menu.select_option', locale=config['language'])}[/bold cyan]",
            choices=["1", "2", "3"]
        )
        logger.info(f"Выбрана опция: {choice}")
        if choice == "1":
            os.system("cls" if os.name == "nt" else "clear")
            running = True
            await run_parse_func(config)
            running = False
        elif choice == "2":
            change_language(config)
        elif choice == "3":
            console.print(f"[cyan]{t('menu.goodbye', locale=config['language'])}[/cyan]")
            break
        input(t("menu.press_enter", locale=config['language']))