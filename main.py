"""Точка входа в игру тамагочи-кликер"""

import os
import random
import textwrap

from game.clicker import SimpleRandomClicker
from game.exceptions import EmptyBagError, NotEnoughMoney, TamagochiIsGone
from game.game import SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi

MENU_WIDTH = 62  # ширина рамки главного меню

MENU_ITEMS = [
    "1. Пойти на работу",
    "2. Купить еду",
    "3. Купить лекарство",
    "4. Покормить",
    "5. Вылечить",
    "6. Играть",
    "7. Отдых",
    "0. Выход",
]

PETS: list[tuple[str, str]] = [
    (
        "Улитка",
        "┈┈╭━━━━━╮┈┈┈┈┈\n"
        "┈┈┃╭━━━╮┃┈┈┈┈┈\n"
        "┈┈┃┃╭━╮┃┃┈◯◯┈┈\n"
        "┈┈┃┃╰━━╯┃╭┻┻╮┈\n"
        "┈╭┻┻━━━━┻╯◒◒┃┈\n"
        "┈╰━━━━━━━━╰╯╯┈",
    ),
    (
        "Злая улитка",
        "┈┈╭━━━━━╮┈┈┈┈┈┈\n"
        "┈┈┃╭━━━╮┃┈┈┈┈┈┈\n"
        "┈┈┃┃╭━╮┃┃┈┈△△┈┈\n"
        "┈┈┃┃╰━━╯┃╭━┻┻━╮\n"
        "┈╭┻┻━━━━┻╯╰◣◢╯┃\n"
        "┈╰━━━━━━━━┏┳┳┓╯",
    ),
    (
        "Лисичка",
        "┈┈▕▔╲┈┈┈┈┈┈┈╱▔▏┈\n"
        "┈┈┈▏╲╲┈┈┈┈┈╱╱▕┈┈\n"
        "┈┈┈▏╱╱▔▔▔▔▔╲╲▕┈┈\n"
        "┈┈╱▅▃▂┊┊┊┊┊▂▃▅╲┈\n"
        "┈╱╱╲▕▇╲┊┊┊╱▇▏╱╲╲\n"
        "▕╱╱╱▔▔▔▏┊▕▔▔▔╲╲╲▏\n"
        "┈╲╱╱╱╱╱▕▇▏╲╲╲╲╲╱\n"
        "┈┈▔▔▔▔╲╰━╯╱▔",
    ),
    (
        "Ослик",
        "╱╲┈┈┈╱╲\n"
        "▏▏▏┈▕▕▕\n"
        "▏▏▏┈▕▕▕\n"
        "▏▏▏┈▕▕▕\n"
        "▏▏▏┈▕▕▕\n"
        "╲▕▂▂▂▏╱\n"
        "╱╭┈┈╭┈╲\n"
        "▏▕▉▔▏▉▔▏\n"
        "▏▕▂╱┈╲▂▏\n"
        "▏┈┈┈┈┈┈╲\n"
        "▏┈┈┈┈┈┈┈╲\n"
        "╲┈┈┈┈▊┈┈▊▏\n"
        "┈▔╲┈┳┈┈┈┈▏\n"
        "┈┈┈╲╰━━━╱\n"
        "┈┈┈┈▔▔▔▔",
    ),
]


def choose_pet() -> tuple[str, str]:
    """
    Предлагает игроку выбрать питомца из списка

    Ввод '0' означает случайный выбор питомца.

    :return: кортеж (имя питомца, ASCII-арт питомца)
    """
    print("Добро пожаловать в тамагочи-кликер!")
    print("Выберите питомца (0 — случайный):")
    for index, (name, _) in enumerate(PETS, start=1):
        print(f"{index}. {name}")
    while True:
        choice = input("Ваш выбор: ")
        if choice == "0":
            return random.choice(PETS)
        if choice.isdigit() and 1 <= int(choice) <= len(PETS):
            return PETS[int(choice) - 1]
        print("Неверный ввод, попробуйте ещё раз")


def row(text: str = "") -> str:
    """
    Строка рамки с текстом у левого края

    :param text: текст строки
    :return: строку с боковыми границами рамки
    """
    return f"║{text.ljust(MENU_WIDTH)}║"


def centered_row(text: str = "") -> str:
    """
    Строка рамки с текстом по центру

    :param text: текст строки
    :return: строку с боковыми границами рамки
    """
    return f"║{text.center(MENU_WIDTH)}║"


def wrapped_rows(text: str) -> list[str]:
    """
    Разбивает длинный текст на несколько строк рамки по ширине меню

    :param text: исходный текст
    :return: список готовых строк рамки
    """
    lines = textwrap.wrap(text, MENU_WIDTH) or [""]
    return [row(line) for line in lines]


def build_menu(game: SimpleGame, pet_name: str, pet_art: str) -> str:
    """
    Собирает главный экран игры в рамке

    :param game: объект игры
    :param pet_name: имя питомца
    :param pet_art: ASCII-арт питомца
    :return: многострочный текст главного экрана
    """
    status = game.get_status()

    lines = [centered_row(pet_name), centered_row()]
    lines.extend(centered_row(art_line) for art_line in pet_art.splitlines())
    lines.append(centered_row())
    lines.extend(wrapped_rows(f"Сумка с едой: {game.food}"))
    lines.extend(wrapped_rows(f"Сумка с лекарствами: {game.medicine}"))
    lines.append(row())
    lines.extend(
        wrapped_rows(
            f"Голод: {status['hunger']} | Здоровье: {status['hp']} | "
            f"Энергия: {status['energy']} | Монет: {status['coins']}"
        )
    )
    if game.tamagochi.is_sick():
        lines.extend(
            wrapped_rows("Внимание: питомец болеет — отдых менее эффективен!")
        )
    lines.append("╠" + "═" * MENU_WIDTH + "╣")
    lines.extend(row(item) for item in MENU_ITEMS)
    lines.append("╚" + "═" * MENU_WIDTH + "╝")
    return "\n".join(["╔" + "═" * MENU_WIDTH + "╗", *lines])


def main() -> None:
    """Точка входа: выбор питомца, создание сущностей и игровой цикл"""
    pet_name, pet_art = choose_pet()

    all_food = [
        Food(name="Бургер", satiety=20, price=40),
        Food(name="Салат", satiety=10, price=20),
        Food(name="Яблоко", satiety=10, price=15),
    ]
    all_medicine = [
        Medicine(name="Ибупрофен", price=30, heal_hp=20, number_of_uses=2),
    ]

    tamagochi = SimpleTamagochi(name=pet_name)
    clicker = SimpleRandomClicker(5, 15)
    game = SimpleGame(tamagochi, clicker, all_food, all_medicine)

    output = f"Вы выбрали питомца: {pet_name}"

    while True:
        os.system("clear")
        print(output)
        print(build_menu(game, pet_name, pet_art))

        if not game.tamagochi.is_alive():
            print("======Питомец погиб... Игра окончена======")
            break

        try:
            match input("\nВыберите действие: "):
                case "1":
                    income = game.work()
                    output = f"Вы заработали {income} монет"
                    game.tamagochi.update()
                case "2":
                    game.buy_food()
                    output = "Еда куплена"
                case "3":
                    game.buy_medicine()
                    output = "Лекарство куплено"
                case "4":
                    game.feed_tamagochi()
                    output = "Питомец накормлен"
                case "5":
                    game.heal_tamagochi()
                    output = "Питомец полечен"
                case "6":
                    game.play_with_tamagochi()
                    output = "Вы поиграли с питомцем"
                case "7":
                    game.rest_tamagochi()
                    output = "Питомец отдохнул"
                case "0":
                    break
                case _:
                    output = "Неверная команда"
        except NotEnoughMoney as error:
            output = str(error)
        except EmptyBagError as error:
            output = str(error)
        except TamagochiIsGone:
            print("======Питомец погиб... Игра окончена======")
            break


if __name__ == "__main__":
    main()
