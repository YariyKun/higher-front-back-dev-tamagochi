"""Модуль с интерфейсом и реализацией класса игры"""

from abc import ABC, abstractmethod
from typing import Any

from .tamagochi import AbstractTamagochi
from .clicker import AbstractClicker
from .models import Food, Medicine
from .exceptions import EmptyBagError, NotEnoughMoney, TamagochiIsGone

START_COINS = 100  # стартовый капитал игрока


class AbstractGame(ABC):
    """Интерфейс для логики игры"""

    @abstractmethod
    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine],
    ):
        """
        Абстрактный метод инициализации класса игры

        :param tamagochi: экземпляр тамагочи
        :param clicker: экземпляр кликера
        :param all_food: все доступные варианты еды
        :param all_medicine: все доступные варианты лекарств
        """
        raise NotImplementedError

    @abstractmethod
    def work(self) -> int:
        """
        Абстрактный метод для логики действия "работа

        :return: количество заработанных монет
        """
        raise NotImplementedError

    @abstractmethod
    def buy_food(self) -> None:
        """Абстрактный метод для покупки еды"""
        raise NotImplementedError

    @abstractmethod
    def buy_medicine(self) -> None:
        """Абстрактный метод для покупки лекарства"""
        raise NotImplementedError

    @abstractmethod
    def feed_tamagochi(self) -> None:
        """Абстрактный метод для кормления тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def heal_tamagochi(self) -> None:
        """Абстрактный метод для лечения тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def rest_tamagochi(self):
        """Абстрактный метод для отдыха тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def play_with_tamagochi(self):
        """Абстрактный метод для игры с тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Абстрактный метод для получения статуса (всех характеристик) тамагочи

        :return: словарь со всеми характеристиками тамагочи
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def food(self) -> list[Food]:
        """
        Абстрактное свойство для доступа к сумке с едой

        :return: список с имеющимися (купленными) объектами еды
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def medicine(self) -> list[Medicine]:
        """
        Абстрактное свойство для доступа к сумке с лекарствами

        :return: список с имеющимися (купленными) объектами лекарств
        """
        raise NotImplementedError


class SimpleGame(AbstractGame):
    """Реализация игры: управляет кошельком и сумками с предметами.

    Игра не знает внутренностей питомца и кликера — только делегирует
    им действия через контракты и следит за ресурсами (монеты, еда,
    лекарства).
    """

    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine],
    ) -> None:
        """
        Инициализация игры

        :param tamagochi: экземпляр тамагочи
        :param clicker: экземпляр кликера
        :param all_food: все доступные варианты еды
        :param all_medicine: все доступные варианты лекарств
        """
        self._tamagochi = tamagochi
        self._clicker = clicker
        self._all_food = all_food
        self._all_medicine = all_medicine
        self._food_bag: list[Food] = []
        self._medicine_bag: list[Medicine] = []
        self._coins = START_COINS

    @property
    def tamagochi(self) -> AbstractTamagochi:
        """
        Свойство для доступа к питомцу

        :return: экземпляр тамагочи
        """
        return self._tamagochi

    @property
    def food(self) -> list[Food]:
        """
        Свойство для доступа к сумке с едой

        :return: список купленных объектов еды
        """
        return self._food_bag

    @property
    def medicine(self) -> list[Medicine]:
        """
        Свойство для доступа к сумке с лекарствами

        :return: список купленных объектов лекарств
        """
        return self._medicine_bag

    def work(self) -> int:
        """
        Отправить питомца на работу: кликер зарабатывает монеты

        :return: количество заработанных монет
        """
        self._clicker.click()
        income = self._clicker.income_per_click
        self._coins += income
        return income

    def buy_food(self) -> None:
        """
        Купить еду в магазин и положить в сумку

        :raises NotEnoughMoney: если не хватает монет
        """
        food = self._choose_item(self._all_food, "Какую еду купить: ")
        if food is None:
            return
        if self._coins < food.price:
            raise NotEnoughMoney(
                f"Не хватает монет: нужно {food.price}, есть {self._coins}"
            )
        self._coins -= food.price
        self._food_bag.append(food)
        print(f"Куплено: {food.name}")

    def buy_medicine(self) -> None:
        """
        Купить лекарство в магазин и положить в сумку

        :raises NotEnoughMoney: если не хватает монет
        """
        medicine = self._choose_item(
            self._all_medicine, "Какое лекарство купить: "
        )
        if medicine is None:
            return
        if self._coins < medicine.price:
            raise NotEnoughMoney(
                f"Не хватает монет: нужно {medicine.price}, есть {self._coins}"
            )
        self._coins -= medicine.price
        self._medicine_bag.append(self._copy_medicine(medicine))
        print(f"Куплено: {medicine.name}")

    def feed_tamagochi(self) -> None:
        """
        Покормить питомца едой из сумки

        :raises TamagochiIsGone: если питомец мёртв
        :raises EmptyBagError: если сумка с едой пуста
        """
        self._ensure_alive()
        if not self._food_bag:
            raise EmptyBagError("Сумка с едой пуста — сначала купите еду")
        food = self._choose_item(self._food_bag, "Чем покормить: ")
        if food is None:
            return
        self._food_bag.remove(food)
        self._tamagochi.feed(food)
        self._tamagochi.update()

    def heal_tamagochi(self) -> None:
        """
        Вылечить питомца лекарством из сумки.
        Пустое лекарство выбрасывается из сумки

        :raises TamagochiIsGone: если питомец мёртв
        :raises EmptyBagError: если сумка с лекарствами пуста
        """
        self._ensure_alive()
        if not self._medicine_bag:
            raise EmptyBagError("Сумка с лекарствами пуста")
        medicine = self._choose_item(self._medicine_bag, "Чем полечить: ")
        if medicine is None:
            return
        self._tamagochi.heal(medicine)
        if medicine.is_empty():
            self._medicine_bag.remove(medicine)
        self._tamagochi.update()

    def rest_tamagochi(self) -> None:
        """
        Уложить питомца отдыхать

        :raises TamagochiIsGone: если питомец мёртв
        """
        self._ensure_alive()
        self._tamagochi.rest()
        self._tamagochi.update()

    def play_with_tamagochi(self) -> None:
        """
        Поиграть с питомцем

        :raises TamagochiIsGone: если питомец мёртв
        """
        self._ensure_alive()
        self._tamagochi.play()
        self._tamagochi.update()

    def get_status(self) -> dict[str, Any]:
        """
        Получить статус игры: показатели питомца и монеты

        :return: словарь со всеми характеристиками
        """
        status: dict[str, Any] = dict(self._tamagochi.status)
        status["coins"] = self._coins
        return status

    def _ensure_alive(self) -> None:
        """
        Проверить, что питомец жив

        :raises TamagochiIsGone: если питомец мёртв
        """
        if not self._tamagochi.is_alive():
            raise TamagochiIsGone("Питомец погиб")

    def _copy_medicine(self, medicine: Medicine) -> Medicine:
        """
        Создать новый экземпляр лекарства, чтобы счётчик использований
        не был общим с каталогом

        :param medicine: лекарство-образец из каталога
        :return: независимую копию лекарства
        """
        return Medicine(
            name=medicine.name,
            price=medicine.price,
            heal_hp=medicine.heal_hp,
            number_of_uses=medicine.number_of_uses,
        )

    def _choose_item(self, items: list[Any], prompt: str) -> Any | None:
        """
        Показать нумерованный список и запросить выбор пользователя

        :param items: список объектов для выбора
        :param prompt: приглашение ко вводу
        :return: выбранный объект или None при отмене (ввод 0)
        """
        for index, item in enumerate(items, start=1):
            print(f"{index}. {item}")
        while True:
            choice = input(prompt)
            if choice == "0":
                return None
            if choice.isdigit() and 1 <= int(choice) <= len(items):
                return items[int(choice) - 1]
            print("Неверный ввод, попробуйте ещё раз (0 — отмена)")
