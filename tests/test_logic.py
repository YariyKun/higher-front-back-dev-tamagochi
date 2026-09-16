import importlib
import sys
import pytest
from conftest import fake_inputs


def _status(obj):
    val = getattr(obj, "status", None)
    assert val is not None, (
        f"Убедитесь, что у объекта `{type(obj).__name__}` определён атрибут/свойство `status`."
    )
    res = val() if callable(val) else val
    assert isinstance(res, dict), (
        "Убедитесь, что `status` является словарём (или методом/свойством, возвращающим словарь)."
    )
    return dict(res)


def _raise_hunger(tama, max_steps=50):
    for _ in range(max_steps):
        if _status(tama)["hunger"] > 0:
            return
        try:
            tama.play()
        except Exception:
            pass
        try:
            tama.update()
        except Exception:
            pass
    pytest.skip("Не удалось повысить голод питомца до > 0 для корректной проверки кормления.")


def _drain_energy(tama, max_steps=60):
    e0 = _status(tama)["energy"]
    for _ in range(max_steps):
        try:
            tama.play()
        except Exception:
            pass
        try:
            tama.update()
        except Exception:
            pass
        if _status(tama)["energy"] < e0:
            return
    pytest.skip("Не удалось снизить энергию питомца для проверки отдыха.")


def _inflict_damage(tama, max_steps=120):
    hp0 = _status(tama)["hp"]
    for _ in range(max_steps):
        try:
            tama.play()
        except Exception:
            pass
        try:
            tama.update()
        except Exception:
            pass
        if _status(tama)["hp"] < hp0:
            return
    pytest.skip("Не удалось уменьшить здоровье питомца для проверки лечения.")


def _ensure_coins(game, target, max_steps=200):
    for _ in range(max_steps):
        if game.get_status()["coins"] >= target:
            return
        game.work()
    raise AssertionError(
        "Убедитесь, что действие `work()` позволяет заработать монеты "
    )


def test_main_import_and_exit():
    try:
        main_mod = importlib.import_module("main")
    except Exception as error:
        raise AssertionError(
            "Убедитесь, что модуль `main` импортируется без ошибок "
            f"{type(error).__name__}: {error})."
        )
    assert hasattr(main_mod, "main") and callable(main_mod.main), (
        "Убедитесь, что в модуле `main` объявлена функция `main()`."
    )
    with fake_inputs(["0"]):
        try:
            main_mod.main()
        except Exception as error:
            raise AssertionError(
                "Убедитесь, что при вводе '0' функция `main()` корректно завершает работу без исключений.\n"
                f"`{type(error).__name__}: {error}`."
            )


def test_game_status(make_game):
    game, *_ = make_game()
    s = game.get_status()
    for key in ("hunger", "hp", "energy", "coins"):
        assert key in s, f"В статусе должен быть ключ `{key}`."
        assert isinstance(s[key], int), f"Значение `{key}` должно быть целым числом."


def test_tamagochi_feed_hunger(make_tamagochi, sample_food):
    tama = make_tamagochi()
    _raise_hunger(tama)
    before = _status(tama)["hunger"]
    tama.feed(sample_food)
    after = _status(tama)["hunger"]
    assert after < before, "Убедитесь, что после кормления голод уменьшается."


def test_tamagochi_rest_increases_energy(make_tamagochi):
    tama = make_tamagochi()
    _drain_energy(tama)
    before = _status(tama)["energy"]
    tama.rest()
    after = _status(tama)["energy"]
    assert after > before, (
        "Убедитесь, что отдых увеличивает энергию, когда она не на максимуме."
    )


def test_tamagochi_heal_increases_hp(make_tamagochi, sample_medicine):
    tama = make_tamagochi()
    _inflict_damage(tama)
    before = _status(tama)["hp"]
    tama.heal(sample_medicine)
    after = _status(tama)["hp"]
    assert after > before, "Убедитесь, что лечение увеличивает здоровье."


def test_tamagochi_play_changes_state(make_tamagochi):
    tama = make_tamagochi()
    s0 = _status(tama)
    try:
        tama.play()
    except Exception as e:
        raise AssertionError("Убедитесь, что метод `play()` выполняется без исключений.") from e
    s1 = _status(tama)
    changed = any(s1[k] != s0[k] for k in ("hunger", "hp", "energy"))
    assert changed, (
        "Убедитесь, что `play()` изменяет хотя бы один из показателей (голод/здоровье/энергия)."
    )


def test_tamagochi_update_progress_or_end(make_tamagochi):
    try:
        from game.exceptions import TamagochiIsGone
    except Exception:
        class TamagochiIsGone(Exception):
            pass

    tama = make_tamagochi()
    s0 = _status(tama)
    ended = False

    for _ in range(300):
        try:
            tama.update()
        except TamagochiIsGone:
            ended = True
            break
        except Exception:
            raise

        s = _status(tama)
        if s.get("hp", 1) <= 0:
            ended = True
            break
        try:
            if hasattr(tama, "is_alive") and tama.is_alive() is False:
                ended = True
                break
        except Exception:
            ended = True
            break

    if not ended:
        s1 = _status(tama)
        assert any(s1[k] != s0[k] for k in ("hunger", "hp", "energy")), (
            "Убедитесь, что вызовы `update()` изменяют состояние питомца, "
            "если игра ещё не завершилась."
        )


def test_work_increases_coins_and_calls_click(make_game):
    game, _, clicker = make_game()

    before = game.get_status()["coins"]
    result = game.work()

    assert isinstance(result, int), "Убедитесь, что `work()` возвращает целое число."
    after = game.get_status()["coins"]
    assert after > before, "Убедитесь, что после `work()` количество монет увеличивается."
    assert getattr(clicker, "clicks", 0) >= 1, (
        "Убедитесь, что `work()` вызывает `clicker.click()` хотя бы один раз."
    )


def test_game_buy_food_adds_inventory(make_game, game_modules):
    Food = game_modules["models"].Food
    game, *_ = make_game(food=[Food(name="Тест-Еда", satiety=5, price=0)])
    before_len = len(getattr(game, "food"))
    with fake_inputs(["1", "0"]):
        game.buy_food()
    after_len = len(getattr(game, "food"))
    assert after_len > before_len, "Убедитесь, что покупка еды добавляет её в инвентарь."


def test_game_feed_removes_selected_item_from_inventory(make_game, game_modules):
    Food = game_modules["models"].Food
    game, tama, _ = make_game(food=[Food(name="Теста-еда", satiety=5, price=0)])

    with fake_inputs(["1", "0"]):
        game.buy_food()
    assert len(game.food) >= 1, (
        "Убедитесь, что покупка еды добавляет её в инвентарь."
    )
    selected = game.food[0]

    _raise_hunger(tama)

    with fake_inputs(["1"]):
        game.feed_tamagochi()

    assert selected not in game.food, (
        "Убедитесь, что после кормления выбранная еда удаляется из списка инвентаря `game.food`."
    )


def test_game_buy_medicine_adds_inventory(make_game, game_modules):
    Medicine = game_modules["models"].Medicine
    game, *_ = make_game(meds=[Medicine(name="Тест-Лекарство", price=0, heal_hp=5, number_of_uses=1)])
    before_len = len(getattr(game, "medicine"))
    with fake_inputs(["1", "0"]):
        game.buy_medicine()
    after_len = len(getattr(game, "medicine"))
    assert after_len > before_len, "Убедитесь, что покупка лекарства добавляет его в инвентарь."


def test_game_end_condition_reachable(make_game):
    try:
        from game.exceptions import TamagochiIsGone
    except Exception:
        class TamagochiIsGone(Exception):
            pass

    game, tama, _ = make_game()
    ended = False
    for _ in range(500):
        try:
            tama.update()
        except TamagochiIsGone:
            ended = True
            break
        s = _status(tama)
        if s.get("hp", 1) <= 0:
            ended = True
            break
        try:
            if hasattr(tama, "is_alive") and tama.is_alive() is False:
                ended = True
                break
        except Exception:
            ended = True
            break

    assert ended, (
        "Убедитесь, что игра имеет конечное состояние: питомец может умереть, "
        "`is_alive()` возвращает `False` или выбрасывается исключение окончания игры."
    )
