from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


LOG_DIRECTORY = Path(__file__).resolve().parent / "logs"


def number(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, ""))
    except (TypeError, ValueError):
        return default


def integer(row: dict[str, str], key: str, default: int = 0) -> int:
    value = row.get(key, "")
    try:
        return int(value, 0)
    except (TypeError, ValueError):
        return default


def latest_csv() -> Path:
    files = sorted(LOG_DIRECTORY.glob("arm_telemetry_*.csv"), key=lambda path: path.stat().st_mtime)
    if not files:
        raise SystemExit(f"В {LOG_DIRECTORY} пока нет журналов arm_telemetry_*.csv")
    return files[-1]


def analyze(path: Path) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    axis_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    driver_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    events = Counter(row.get("event", "") for row in rows)

    for row in rows:
        axis = row.get("axis", "")
        if row.get("event") == "AXIS" and axis:
            axis_rows[axis].append(row)
        elif row.get("event") == "TMCDETAIL" and axis:
            driver_rows[axis].append(row)

    print(f"Файл: {path}")
    print(f"Всего строк CSV: {len(rows)}")
    print(f"События: {dict(events)}")

    for axis in ("1", "2"):
        motion = axis_rows[axis]
        telemetry = driver_rows[axis]
        print(f"\n=== ОСЬ {axis} ===")
        if motion:
            print(f"Максимальная заданная скорость: {max(number(r, 'target_pps') for r in motion):.0f} имп/с")
            print(f"Максимальная командная скорость RMT: {max(abs(number(r, 'current_pps')) for r in motion):.1f} имп/с")
            print(f"Максимальная скорость выхода: {max(abs(number(r, 'output_deg_s')) for r in motion):.2f} °/с")
            print(f"Диапазон относительного счётчика: {min(number(r, 'position_deg_rel') for r in motion):.2f}…{max(number(r, 'position_deg_rel') for r in motion):.2f}°")
        else:
            print("Нет записей движения")

        if not telemetry:
            print("Нет телеметрии TMC2209")
            continue

        online = sum(row.get("uart") == "ONLINE" for row in telemetry)
        print(f"UART ONLINE: {online}/{len(telemetry)}")
        modes = Counter(row.get("mode", "?") for row in telemetry if row.get("uart") == "ONLINE")
        requested_modes = Counter(row.get("requested_mode", "?") for row in telemetry)
        print(f"Фактические режимы: {dict(modes)}")
        print(f"Запрошенные режимы: {dict(requested_modes)}")

        moving_sg = [
            integer(row, "sg_result")
            for row in telemetry
            if row.get("uart") == "ONLINE" and integer(row, "standstill", 1) == 0
        ]
        if moving_sg:
            print(f"SG_RESULT в движении: min={min(moving_sg)}, max={max(moving_sg)}, samples={len(moving_sg)}")
        else:
            print("SG_RESULT в движении: нет валидных отсчётов")

        print(
            "CS_ACTUAL: "
            f"min={min(integer(r, 'cs_actual') for r in telemetry)}, "
            f"max={max(integer(r, 'cs_actual') for r in telemetry)} из 31"
        )
        print(
            "PWM_SCALE_SUM: "
            f"min={min(integer(r, 'pwm_scale_sum') for r in telemetry)}, "
            f"max={max(integer(r, 'pwm_scale_sum') for r in telemetry)}"
        )

        alarm_fields = (
            "otpw",
            "ot",
            "t120",
            "t143",
            "t150",
            "t157",
            "short_a",
            "short_b",
        )
        alarms = {field: sum(integer(row, field) != 0 for row in telemetry) for field in alarm_fields}
        print(f"Срабатывания температур/КЗ: {alarms}")

        moving_open_a = sum(
            integer(row, "open_a") != 0 and integer(row, "standstill", 1) == 0
            for row in telemetry
        )
        moving_open_b = sum(
            integer(row, "open_b") != 0 and integer(row, "standstill", 1) == 0
            for row in telemetry
        )
        print(f"OPEN_LOAD во время движения: фаза A={moving_open_a}, фаза B={moving_open_b}")

    marks = [row for row in rows if row.get("event") == "MARK"]
    if marks:
        print("\n=== РУЧНЫЕ МЕТКИ ===")
        for row in marks:
            print(f"{row.get('time_local', '?')}: {row.get('message', '')}")

    print("\nВажно: current_pps — частота команд STEP, а не измеренная скорость ротора.")
    print("Без энкодеров журнал не может доказать, что двигатель физически не пропустил шаг.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Сводка журнала роборуки")
    parser.add_argument("csv_file", nargs="?", type=Path, help="CSV; без аргумента берётся последний")
    args = parser.parse_args()
    analyze(args.csv_file.resolve() if args.csv_file else latest_csv())


if __name__ == "__main__":
    main()
