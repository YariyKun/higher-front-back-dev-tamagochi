"""Модуль с интерфейсом и реализацией кликера"""

import random
from abc import ABC, abstractmethod


class AbstractClicker(ABC):
    """Интерфейс для кликера"""

    @abstractmethod
    def __init__(self) -> None:
        """Абстрактный метод инициализации"""
        raise NotImplementedError

    @abstractmethod
    def click(self) -> None:
        """Абстрактный метод клика для накапливания монет"""
        raise NotImplementedError

    @property
    @abstractmethod
    def income_per_click(self) -> int:
        """Абстрактное свойство для доступа к количеству монет за клик"""
        raise NotImplementedError


class SimpleRandomClicker(AbstractClicker):
    """Кликер, начисляющий за клик случайное количество монет

    При каждом клике доход генерируется заново в диапазоне
    [min_income, max_income] включительно.
    """

    def __init__(self, min_income: int, max_income: int) -> None:
        """Инициализация кликера

        :param min_income: минимальный доход за клик
        :param max_income: максимальный доход за клик
        :raises ValueError: если min_income больше max_income
        """
        if min_income > max_income:
            raise ValueError("min_income не может быть больше max_income")
        self._min_income = min_income
        self._max_income = max_income
        self._income_per_click = 0

    @property
    def income_per_click(self) -> int:
        """Свойство для доступа к количеству монет за последний клик

        :return: доход последнего клика, 0 если кликов ещё не было.
        """
        return self._income_per_click

    def click(self) -> None:
        """Совершает клик: генерирует случайный доход и запоминает его."""
        self._income_per_click = random.randint(
            self._min_income,
            self._max_income,
        )
