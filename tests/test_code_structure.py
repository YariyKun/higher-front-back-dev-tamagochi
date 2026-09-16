import inspect
import pytest


EXPECTED_MODULE_KEYS = ("clicker", "game", "tamagochi", "models", "exceptions")

@pytest.mark.parametrize("name", EXPECTED_MODULE_KEYS, ids=EXPECTED_MODULE_KEYS)
def test_modules_present(game_modules, name):
    assert name in game_modules, f"Убедитесь, что модуль `game.{name}` существует."
    assert game_modules[name] is not None, f"Модуль `game.{name}` должен импортироваться."


@pytest.mark.parametrize(
    "cls_name",
    ("Food", "Medicine"),
    ids=["Food", "Medicine"],
)
def test_models_exist(game_modules, cls_name):
    models = game_modules["models"]
    assert hasattr(models, cls_name), (
        f"Убедитесь, что в модуле `game.models` определена модель `{cls_name}`."
    )


@pytest.mark.parametrize(
    "exc_name",
    ("TamagochiIsGone", "NotEnoughMoney"),
    ids=["TamagochiIsGone", "NotEnoughMoney"],
)
def test_exceptions_exist(game_modules, exc_name):
    exceptions = game_modules["exceptions"]
    assert hasattr(exceptions, exc_name), (
        f"Убедитесь, что в модуле `game.exceptions` определено исключение `{exc_name}`."
    )
    obj = getattr(exceptions, exc_name)
    assert inspect.isclass(obj) and issubclass(obj, Exception), (
        f"`{exc_name}` должно быть классом и наследоваться от `Exception`."
    )


EXPECTED_ABSTRACTS = (
    ("clicker",   "AbstractClicker",   ["__init__", "click", "income_per_click"], "AbstractClicker"),
    ("tamagochi", "AbstractTamagochi", ["feed", "play", "rest", "heal", "status", "is_alive", "is_sick", "update"], "AbstractTamagochi"),
    ("game",      "AbstractGame",      ["__init__", "work", "buy_food", "buy_medicine",
                                        "feed_tamagochi", "heal_tamagochi", "rest_tamagochi",
                                        "play_with_tamagochi", "get_status", "food", "medicine"], "AbstractGame"),
)


@pytest.mark.parametrize(
    "module_key, class_name, expected_attrs, _id",
    EXPECTED_ABSTRACTS,
    ids=[t[-1] for t in EXPECTED_ABSTRACTS],
)
def test_abstract_interfaces_shape(game_modules, module_key, class_name, expected_attrs, _id):
    mod = game_modules[module_key]
    assert hasattr(mod, class_name), (
        f"Убедитесь, что в модуле `game.{module_key}` определён класс `{class_name}`."
    )
    cls = getattr(mod, class_name)
    assert inspect.isclass(cls), f"`{class_name}` должен быть классом."
    missing = [name for name in expected_attrs if not hasattr(cls, name)]
    assert not missing, (
        f"Убедитесь, что в классе `{class_name}` определены все необходимые методы/свойства.\n"
        f"Отсутствуют: {', '.join(missing)}"
    )


def _concrete_impls(mod, base_cls):
    out = []
    for obj in vars(mod).values():
        if inspect.isclass(obj) and issubclass(obj, base_cls) and obj is not base_cls:
            if not getattr(obj, "__abstractmethods__", set()):
                out.append(obj)
    return out

EXPECTED_IMPL_BASES = (
    ("clicker",   "AbstractClicker",   "класс наследник"),
    ("tamagochi", "AbstractTamagochi", "класс наследник"),
    ("game",      "AbstractGame",      "класс наследник"),
)


@pytest.mark.parametrize(
    "module_key, base_name, human",
    EXPECTED_IMPL_BASES,
    ids=[f"{m}::{b}" for m, b, _ in EXPECTED_IMPL_BASES],
)
def test_concrete_implementation_exists(game_modules, module_key, base_name, human):
    mod = game_modules[module_key]
    assert hasattr(mod, base_name), (
        f"В модуле `game.{module_key}` должен быть класс `{base_name}`."
    )
    base = getattr(mod, base_name)
    impls = _concrete_impls(mod, base)
    assert impls, f"В `game.{module_key}` добавьте {human} абстрактного класса `{base_name}`."


def test_main_symbol_exists():
    import importlib
    try:
        main = importlib.import_module("main")
    except Exception as e:
        raise AssertionError(
            "Не удалось импортировать модуль `main`. "
            "Убедитесь, что код не выполняет `main()` в глобальной области.\n"
            f"{type(e).__name__}: {e}"
        )
    assert hasattr(main, "main") and callable(main.main), (
        "В модуле `main` должна быть определена функция `main`."
    )
