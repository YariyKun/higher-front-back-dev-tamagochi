import builtins
import importlib
import contextlib
import inspect
import os
import sys
from pathlib import Path

import pytest


BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(BASE_DIR))


def _import_or_fail(module_name):
    try:
        return importlib.import_module(module_name)
    except Exception as e:
        raise AssertionError(
            f"При импорте модуля `{module_name}` произошла ошибка:\n"
            f"{type(e).__name__}: {e}"
        )


@pytest.fixture(autouse=True)
def _no_clear(monkeypatch):
    monkeypatch.setattr(os, "system", lambda *args, **kwargs: 0)


@contextlib.contextmanager
def fake_inputs(values):
    it = iter(values)
    real = builtins.input
    def _fake(_=None):
        try:
            return next(it)
        except StopIteration:
            return "0"
    builtins.input = _fake
    try:
        yield
    finally:
        builtins.input = real


@pytest.fixture(scope="session")
def game_modules():
    return {
        "clicker": _import_or_fail("game.clicker"),
        "game": _import_or_fail("game.game"),
        "tamagochi": _import_or_fail("game.tamagochi"),
        "models": _import_or_fail("game.models"),
        "exceptions": _import_or_fail("game.exceptions"),
    }


def _first_concrete_subclass(module, base_cls):
    candidates = []
    for _, obj in vars(module).items():
        if inspect.isclass(obj) and issubclass(obj, base_cls) and obj is not base_cls:
            if not getattr(obj, "__abstractmethods__", set()):
                candidates.append(obj)
    for cls in candidates:
        if cls.__module__ == module.__name__:
            return cls
    return candidates[0] if candidates else None


def _get_model_cls(models_module, cls_name, human_name):
    try:
        return getattr(models_module, cls_name)
    except AttributeError as e:
        raise AssertionError(
            f"Убедитесь, что в файле `game.models.py` определена модель `{human_name}`.\n"
            f"Не удалось найти `{human_name}` в модуле `game.models`.\n"
            f"{type(e).__name__}: {e}"
        )


def _make_food(Food, *, name="Тест-еда", satiety=10, price=5):
    try:
        return Food(name=name, satiety=satiety, price=price)
    except TypeError:
        raise AssertionError(
            "Не получается создать объект `Food(name, satiety, price)`. "
            "Проверьте параметры конструктора."
        )


def _make_medicine(Medicine, *, name="Тест-лекарство", price=10, heal_hp=7, number_of_uses=1):
    try:
        return Medicine(name=name, price=price, heal_hp=heal_hp, number_of_uses=number_of_uses)
    except TypeError:
        raise AssertionError(
            "Не получается создать объект `Medicine(name, price, heal_hp, number_of_uses)`. "
            "Проверьте параметры конструктора."
        )


@pytest.fixture
def sample_food(game_modules):
    Food = _get_model_cls(game_modules["models"], "Food", "Food")
    return _make_food(Food)


@pytest.fixture
def sample_medicine(game_modules):
    Medicine = _get_model_cls(game_modules["models"], "Medicine", "Medicine")
    return _make_medicine(Medicine)


@pytest.fixture
def make_tamagochi(game_modules):
    base = game_modules["tamagochi"].AbstractTamagochi
    impl_cls = _first_concrete_subclass(game_modules["tamagochi"], base)
    assert impl_cls is not None, (
        "Убедитесь, что в файле `game/tamagochi.py` есть класс-наследник `AbstractTamagochi`."
    )

    def _factory():
        try:
            return impl_cls()
        except TypeError:
            raise AssertionError(
                "Убедитесь, что можно создать объект тамагочи без аргументов "
                "(конструктор без обязательных параметров)."
            )
    return _factory


@pytest.fixture
def make_game(game_modules, make_tamagochi):
    models_mod = game_modules["models"]
    Food = _get_model_cls(models_mod, "Food", "Food")
    Medicine = _get_model_cls(models_mod, "Medicine", "Medicine")
    base_game = game_modules["game"].AbstractGame
    impl_cls = _first_concrete_subclass(game_modules["game"], base_game)
    assert impl_cls is not None, (
        "Убедитесь, что в файле `game/game.py` есть класс-наследник `AbstractGame`."
    )

    AbstractClicker = game_modules["clicker"].AbstractClicker

    class _TestClicker(AbstractClicker):
        def __init__(self, income_per_click: int = 7) -> None:
            self._income = income_per_click
            self._clicks = 0

        @property
        def income_per_click(self) -> int:
            return self._income

        def click(self) -> None:
            self._clicks += 1

        @property
        def clicks(self) -> int:
            return self._clicks

    def _factory(food=None, meds=None, click_income=7):
        tamagochi = make_tamagochi()
        clicker = _TestClicker(click_income)

        all_food = food if food is not None else [
            _make_food(Food, name="Бургер", satiety=20, price=40),
            _make_food(Food, name="Салат", satiety=10, price=20),
            _make_food(Food, name="Яблоко", satiety=10, price=15),
        ]
        all_medicine = meds if meds is not None else [
            _make_medicine(Medicine, name="Ибупрофен", price=30, heal_hp=20, number_of_uses=2),
        ]

        try:
            game = impl_cls(tamagochi, clicker, all_food=all_food, all_medicine=all_medicine)
        except TypeError:
            raise AssertionError(
                "Не получается создать объект игры: ожидаются аргументы конструктора "
                "`tamagochi, clicker, all_food, all_medicine` — именно в таком порядке."
            )
        return game, tamagochi, clicker
    return _factory
