"""Модуль с исключениями"""


class TamagochiIsGone(Exception):
    """Ошибка при смерти тамагочи"""


class NotEnoughMoney(Exception):
    """Ошибка когда не хватает монет для покупки"""


class EmptyBagError(Exception):
    """Ошибка при попытке использовать предмет из пустой сумки"""
