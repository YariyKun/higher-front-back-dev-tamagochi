"""Модуль с интерфейсом и реализациями класса тамагочи"""

import random
from abc import ABC, abstractmethod

from .models import Food, Medicine

MAX_STAT = 100  # максимальное значение показателя
START_HUNGER = 40  # стартовый голод питомца

HUNGER_GROWTH = 4  # рост голода за один тик
FEED_ENERGY_COST = 2  # трата энергии при кормлении
PLAY_ENERGY_COST = 20  # трата энергии при игре
PLAY_FATIGUE_COST = 15  # рост усталости при игре
PLAY_HUNGER_COST = 5  # рост голода при игре
REST_ENERGY_RECOVERY = 30  # восстановление энергии за отдых
SICK_REST_ENERGY_RECOVERY = 15  # восстановление энергии при болезни
REST_FATIGUE_RECOVERY = 40  # снятие усталости за отдых

SICK_HP_DAMAGE = 10  # потеря HP за тик во время болезни
SICK_FATIGUE_GROWTH = 5  # рост усталости за тик во время болезни
STARVATION_HP_DAMAGE = 10  # потеря HP за тик при голоде 100
EXHAUSTION_HP_DAMAGE = 5  # потеря HP за тик при усталости 100

BASE_SICK_CHANCE = 0.05  # базовый шанс заболеть за тик
HIGH_FATIGUE_SICK_CHANCE = 0.3  # шанс заболеть при сильной усталости
HIGH_FATIGUE_THRESHOLD = 70  # порог сильной усталости


class AbstractTamagochi(ABC):
    """Интерфейс логики тамагочи"""

    @abstractmethod
    def feed(self, food: Food) -> None:
        """
        Абстрактный метод для кормления тамагочи

        :param food: объект еды для кормления
        """
        raise NotImplementedError

    @abstractmethod
    def play(self) -> None:
        """Абстрактный метод для игры с тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def rest(self) -> None:
        """Абстрактный метод для отдыха тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def heal(self, medicine: Medicine) -> None:
        """
        Абстрактный метод для лечения тамагочи

        :param medicine: лекарство для лечения
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> dict[str, int]:
        """
        Абстрактное свойство для доступа ко всем состояниям тамагочи

        :return: словарь со всеми состояниями тамагочи
        """
        raise NotImplementedError

    @abstractmethod
    def is_alive(self) -> bool:
        """
        Абстрактный метод для проверки жив ли тамагочи

        :return: True если жив, иначе False
        """
        raise NotImplementedError

    @abstractmethod
    def is_sick(self) -> bool:
        """
        Абстрактный метод для проверки, не заболел ли тамагочи

        :return: True если тамагочи болеет, иначе False
        """
        raise NotImplementedError

    @abstractmethod
    def update(self) -> None:
        """
        Абстрактный метод для обновления состояний тамагочи.
        Должен использоваться после каждого взаимодействия с тамагочи
        """
        raise NotImplementedError


class SimpleTamagochi(AbstractTamagochi):
    """Классическая реализация тамагочи

    Голод и усталость растут со временем, при критических значениях
    питомец теряет здоровье и может заболеть. Болезнь ускоряет потерю
    здоровья и делает отдых менее эффективным.
    """

    def __init__(self, name: str = "Питомец") -> None:
        """
        Инициализация питомца со стартовыми показателями

        :param name: имя питомца
        """
        self.name = name
        self._hp = MAX_STAT
        self._hunger = START_HUNGER
        self._fatigue = 0
        self._energy = MAX_STAT
        self._is_sick = False

    def feed(self, food: Food) -> None:
        """
        Накормить питомца: снижает голод, немного тратит энергию

        :param food: объект еды для кормления
        """
        self._hunger = max(0, self._hunger - food.satiety)
        self._energy = max(0, self._energy - FEED_ENERGY_COST)

    def play(self) -> None:
        """Поиграть с питомцем: тратит энергию, повышает голод и усталость"""
        self._energy = max(0, self._energy - PLAY_ENERGY_COST)
        self._fatigue = min(MAX_STAT, self._fatigue + PLAY_FATIGUE_COST)
        self._hunger = min(MAX_STAT, self._hunger + PLAY_HUNGER_COST)

    def rest(self) -> None:
        """
        Уложить питомца отдыхать: восстанавливает энергию
        и снимает усталость. Во время болезни восстановление слабее
        """
        if self._is_sick:
            recovery = SICK_REST_ENERGY_RECOVERY
        else:
            recovery = REST_ENERGY_RECOVERY
        self._energy = min(MAX_STAT, self._energy + recovery)
        self._fatigue = max(0, self._fatigue - REST_FATIGUE_RECOVERY)

    def heal(self, medicine: Medicine) -> None:
        """
        Вылечить питомца: восстанавливает HP и снимает болезнь.
        Увеличивает счётчик использований лекарства

        :param medicine: лекарство для лечения
        """
        self._hp = min(MAX_STAT, self._hp + medicine.heal_hp)
        self._is_sick = False
        medicine.uses += 1

    @property
    def status(self) -> dict[str, int]:
        """
        Текущие показатели питомца

        :return: словарь со значениями голода, усталости, HP и энергии
        """
        return {
            "hunger": self._hunger,
            "fatigue": self._fatigue,
            "hp": self._hp,
            "energy": self._energy,
        }

    def is_alive(self) -> bool:
        """
        Проверить, жив ли питомец

        :return: True, пока здоровье больше нуля, иначе False
        """
        return self._hp > 0

    def is_sick(self) -> bool:
        """
        Проверить, болен ли питомец

        :return: True если питомец болеет, иначе False
        """
        return self._is_sick

    def update(self) -> None:
        """
        Обновить состояние за один тик времени

        Голод растёт, во время болезни теряются здоровье и силы.
        При голоде 100 или усталости 100 питомец теряет здоровье.
        С высокой усталостью повышен шанс заболеть
        """
        self._hunger = min(MAX_STAT, self._hunger + HUNGER_GROWTH)

        if self._is_sick:
            self._hp -= SICK_HP_DAMAGE
            self._fatigue = min(MAX_STAT, self._fatigue + SICK_FATIGUE_GROWTH)

        if self._hunger >= MAX_STAT:
            self._hp -= STARVATION_HP_DAMAGE

        if self._fatigue >= MAX_STAT:
            self._hp -= EXHAUSTION_HP_DAMAGE

        self._hp = max(0, self._hp)

        if not self._is_sick and random.random() < self._sick_chance():
            self._is_sick = True

    def _sick_chance(self) -> float:
        """
        Рассчитать шанс заболеть за тик в зависимости от усталости

        :return: шанс заболеть от 0 до 1
        """
        if self._fatigue >= HIGH_FATIGUE_THRESHOLD:
            return HIGH_FATIGUE_SICK_CHANCE
        return BASE_SICK_CHANCE + self._fatigue / 200
