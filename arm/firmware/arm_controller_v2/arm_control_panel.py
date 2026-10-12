from __future__ import annotations

import csv
import json
import os
import queue
import re
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import ttk

import serial
from serial.tools import list_ports


BAUD_RATE = 115200
PULSES_PER_OUTPUT_DEGREE = 200 * 8 * 71 / 360
MAX_SPEED_PPS = 7258
# 7258 PPS rounds to 23.0 output degrees/second with the 1:71 gearbox.
MAX_OUTPUT_SPEED_DEG_S = MAX_SPEED_PPS / PULSES_PER_OUTPUT_DEGREE
AXIS_RE = re.compile(r"(\w+)=([^\s]+)")
LOG_DIRECTORY = Path(__file__).resolve().parent / "logs"
# Driver diagnostics do not need to compete with motion/configuration traffic.
# Two complete snapshots per second are enough for trends and fault flags.
TELEMETRY_PERIOD_MS = 500
CONFIG_DEBOUNCE_MS = 140

DRIVER_MODE_OPTIONS = (
    "StealthChop — максимально тихо",
    "Гибрид — тихо снизу, тяга сверху",
    "SpreadCycle — максимальная тяга",
)
DRIVER_MODE_COMMANDS = {
    DRIVER_MODE_OPTIONS[0]: "STEALTH",
    DRIVER_MODE_OPTIONS[1]: "HYBRID",
    DRIVER_MODE_OPTIONS[2]: "SPREAD",
}


class SessionLogger:
    CSV_COLUMNS = (
        "time_local",
        "direction",
        "event",
        "axis",
        "name",
        "state",
        "requested",
        "target_pps",
        "current_pps",
        "output_deg_s",
        "accel_pps2",
        "smooth_steps",
        "position_steps",
        "position_deg_rel",
        "uart",
        "version",
        "mode",
        "requested_mode",
        "config_verified",
        "standstill",
        "cs_actual",
        "sg_result",
        "tstep",
        "pwm_scale_sum",
        "pwm_scale_auto",
        "gconf",
        "gstat",
        "chopconf",
        "drv_status",
        "pwmconf",
        "otpw",
        "ot",
        "t120",
        "t143",
        "t150",
        "t157",
        "short_a",
        "short_b",
        "open_a",
        "open_b",
        "message",
        "all_fields_json",
    )

    def __init__(self) -> None:
        LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.raw_path = LOG_DIRECTORY / f"arm_session_{stamp}.log"
        self.csv_path = LOG_DIRECTORY / f"arm_telemetry_{stamp}.csv"
        self.raw_file = self.raw_path.open("a", encoding="utf-8", buffering=1)
        self.csv_file = self.csv_path.open("a", encoding="utf-8-sig", newline="", buffering=1)
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.CSV_COLUMNS)
        self.csv_writer.writeheader()

    @staticmethod
    def timestamp() -> str:
        return datetime.now().astimezone().isoformat(timespec="milliseconds")

    def raw(self, direction: str, line: str) -> None:
        self.raw_file.write(f"{self.timestamp()} [{direction}] {line}\n")

    def record(
        self,
        direction: str,
        event: str,
        fields: dict[str, str] | None = None,
        message: str = "",
    ) -> None:
        values = fields or {}
        row = {column: "" for column in self.CSV_COLUMNS}
        row.update({key: values.get(key, "") for key in self.CSV_COLUMNS if key in values})
        row["time_local"] = self.timestamp()
        row["direction"] = direction
        row["event"] = event
        row["message"] = message
        row["all_fields_json"] = json.dumps(values, ensure_ascii=False, sort_keys=True)
        self.csv_writer.writerow(row)

    def close(self) -> None:
        for file in (self.raw_file, self.csv_file):
            try:
                file.flush()
                file.close()
            except Exception:
                pass


@dataclass(frozen=True)
class AxisDefaults:
    index: int
    title: str
    negative_label: str
    positive_label: str
    speed_deg_s: float
    accel_deg_s2: float
    smooth_steps: int


AXIS_DEFAULTS = (
    AxisDefaults(1, "Нижний механизм — первый драйвер — стрелки ← →", "◀  ВЛЕВО", "ВПРАВО  ▶", 10.0, 20.0, 300),
    AxisDefaults(2, "Верхний механизм — новый драйвер — стрелки ↓ ↑", "▼  ВНИЗ", "ВВЕРХ  ▲", 8.0, 15.0, 400),
)


class SerialLink:
    def __init__(self, incoming: queue.Queue[str]) -> None:
        self.incoming = incoming
        self.port: serial.Serial | None = None
        self.lock = threading.Lock()
        self.reader_thread: threading.Thread | None = None
        self.stop_event = threading.Event()

    @property
    def connected(self) -> bool:
        return self.port is not None and self.port.is_open

    def connect(self, port_name: str) -> None:
        self.disconnect()
        self.stop_event.clear()
        port = serial.Serial(port_name, BAUD_RATE, timeout=0.1, write_timeout=0.5)
        time.sleep(1.2)  # ESP32 normally resets when the COM port opens.
        port.reset_input_buffer()
        self.port = port
        self.reader_thread = threading.Thread(target=self._reader, daemon=True)
        self.reader_thread.start()

    def disconnect(self) -> None:
        self.stop_event.set()
        port, self.port = self.port, None
        if port:
            try:
                port.close()
            except Exception:
                pass

    def send(self, command: str) -> bool:
        port = self.port
        if not port or not port.is_open:
            return False
        try:
            with self.lock:
                port.write((command + "\n").encode("ascii"))
                port.flush()
            return True
        except Exception as exc:
            self.incoming.put(f"LINK_ERROR {exc}")
            return False

    def _reader(self) -> None:
        port = self.port
        while port is self.port and port and port.is_open and not self.stop_event.is_set():
            try:
                line = port.readline().decode("utf-8", "replace").strip()
                if line:
                    self.incoming.put(line)
            except Exception as exc:
                self.incoming.put(f"LINK_ERROR {exc}")
                return


class AxisPanel:
    def __init__(self, app: "ArmControlPanel", parent: ttk.Frame, defaults: AxisDefaults) -> None:
        self.app = app
        self.defaults = defaults
        self.index = defaults.index
        self.active = False
        self._config_after_id: str | None = None

        self.speed_var = tk.DoubleVar(value=defaults.speed_deg_s)
        self.accel_var = tk.DoubleVar(value=defaults.accel_deg_s2)
        self.smooth_var = tk.IntVar(value=defaults.smooth_steps)
        self.invert_var = tk.BooleanVar(value=False)
        self.driver_mode_var = tk.StringVar(value=DRIVER_MODE_OPTIONS[1])
        self.transition_var = tk.DoubleVar(value=3.0)
        self.speed_readout = tk.StringVar()
        self.accel_readout = tk.StringVar()
        self.live_state = tk.StringVar(value="Ожидание данных")
        self.driver_state = tk.StringVar(value="UART: ожидание телеметрии")
        self.driver_temperature = tk.StringVar(value="Температура кристалла: неизвестно")
        self.driver_load = tk.StringVar(value="Нагрузка и токовая шкала: неизвестно")
        self.driver_faults = tk.StringVar(value="Ошибки драйвера: неизвестно")

        self.frame = ttk.LabelFrame(parent, text=defaults.title, padding=16)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        self._build()
        self._update_readouts()

    def _build(self) -> None:
        ttk.Label(self.frame, text="Скорость сустава").grid(row=0, column=0, sticky="w")
        ttk.Label(self.frame, textvariable=self.speed_readout, style="Value.TLabel").grid(
            row=0, column=1, sticky="e"
        )
        speed = tk.Scale(
            self.frame,
            from_=1,
            to=MAX_OUTPUT_SPEED_DEG_S,
            resolution=0.1,
            showvalue=False,
            orient="horizontal",
            variable=self.speed_var,
            command=lambda _value: self._setting_changed(),
            bg="#172033",
            fg="#f8fafc",
            troughcolor="#34415a",
            activebackground="#60a5fa",
            highlightthickness=0,
            bd=0,
        )
        speed.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 10))

        ttk.Label(self.frame, text="Разгон / торможение").grid(row=2, column=0, sticky="w")
        ttk.Label(self.frame, textvariable=self.accel_readout, style="Value.TLabel").grid(
            row=2, column=1, sticky="e"
        )
        accel = tk.Scale(
            self.frame,
            from_=3,
            to=150,
            resolution=1,
            showvalue=False,
            orient="horizontal",
            variable=self.accel_var,
            command=lambda _value: self._setting_changed(),
            bg="#172033",
            fg="#f8fafc",
            troughcolor="#34415a",
            activebackground="#34d399",
            highlightthickness=0,
            bd=0,
        )
        accel.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(2, 10))

        smooth_row = ttk.Frame(self.frame)
        smooth_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(smooth_row, text="S-плавность, STEP:").pack(side="left")
        smooth = ttk.Spinbox(
            smooth_row,
            from_=0,
            to=2000,
            increment=50,
            width=7,
            textvariable=self.smooth_var,
            command=self._setting_changed,
        )
        smooth.pack(side="left", padx=(8, 12))
        smooth.bind("<Return>", lambda _event: self._setting_changed())
        ttk.Checkbutton(
            smooth_row,
            text="Инвертировать направление",
            variable=self.invert_var,
            command=self._setting_changed,
        ).pack(side="left")

        presets = ttk.Frame(self.frame)
        presets.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for column, (name, speed_value, accel_value, smooth_value) in enumerate(
            (
                ("Тихо", 5, 12, 600),
                ("Нормально", 15, 35, 450),
                ("Предел 7258", 23, 35, 600),
            )
        ):
            presets.columnconfigure(column, weight=1)
            ttk.Button(
                presets,
                text=name,
                command=lambda s=speed_value, a=accel_value, j=smooth_value: self.set_profile(s, a, j),
            ).grid(row=0, column=column, padx=3, sticky="ew")

        buttons = ttk.Frame(self.frame)
        buttons.grid(row=6, column=0, columnspan=2, sticky="nsew")
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        negative = tk.Button(
            buttons,
            text=self.defaults.negative_label + "\nудерживать",
            font=("Segoe UI Semibold", 15),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            height=3,
        )
        negative.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        negative.bind("<ButtonPress-1>", lambda _event: self.start(-1))

        positive = tk.Button(
            buttons,
            text=self.defaults.positive_label + "\nудерживать",
            font=("Segoe UI Semibold", 15),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            height=3,
        )
        positive.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        positive.bind("<ButtonPress-1>", lambda _event: self.start(1))

        ttk.Label(self.frame, textvariable=self.live_state, style="Live.TLabel").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

        ttk.Separator(self.frame, orient="horizontal").grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=(12, 10)
        )
        driver_controls = ttk.Frame(self.frame)
        driver_controls.grid(row=9, column=0, columnspan=2, sticky="ew")
        driver_controls.columnconfigure(1, weight=1)
        ttk.Label(driver_controls, text="Режим TMC2209:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            driver_controls,
            textvariable=self.driver_mode_var,
            values=DRIVER_MODE_OPTIONS,
            state="readonly",
            width=34,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 6))
        ttk.Button(
            driver_controls,
            text="ПРИМЕНИТЬ",
            command=self.apply_driver_mode,
        ).grid(row=0, column=2, sticky="e")

        ttk.Label(driver_controls, text="Переход гибрида:").grid(
            row=1, column=0, sticky="w", pady=(7, 0)
        )
        transition = ttk.Spinbox(
            driver_controls,
            from_=1.0,
            to=10.0,
            increment=0.5,
            width=7,
            textvariable=self.transition_var,
        )
        transition.grid(row=1, column=1, sticky="w", padx=(8, 6), pady=(7, 0))
        ttk.Label(driver_controls, text="°/с выхода; применяется только к гибриду").grid(
            row=1, column=1, sticky="w", padx=(72, 0), pady=(7, 0)
        )

        diagnostics = ttk.Frame(self.frame)
        diagnostics.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for row, variable in enumerate(
            (self.driver_state, self.driver_temperature, self.driver_load, self.driver_faults)
        ):
            ttk.Label(
                diagnostics,
                textvariable=variable,
                style="Driver.TLabel",
            ).grid(row=row, column=0, sticky="w", pady=1)

    def _update_readouts(self) -> None:
        speed_deg = float(self.speed_var.get())
        accel_deg = float(self.accel_var.get())
        self.speed_readout.set(f"{speed_deg:.1f} °/с  ·  {self.speed_pps} имп/с")
        self.accel_readout.set(f"{accel_deg:.0f} °/с²  ·  {self.accel_pps2} имп/с²")

    @property
    def speed_pps(self) -> int:
        return max(
            80,
            min(MAX_SPEED_PPS, round(float(self.speed_var.get()) * PULSES_PER_OUTPUT_DEGREE)),
        )

    @property
    def accel_pps2(self) -> int:
        return max(200, min(100000, round(float(self.accel_var.get()) * PULSES_PER_OUTPUT_DEGREE)))

    def config_command(self) -> str:
        try:
            smooth = max(0, min(2000, int(self.smooth_var.get())))
        except (tk.TclError, ValueError):
            smooth = self.defaults.smooth_steps
            self.smooth_var.set(smooth)
        return (
            f"CONFIG {self.index} {self.speed_pps} {self.accel_pps2} "
            f"{smooth} {1 if self.invert_var.get() else 0}"
        )

    def _setting_changed(self) -> None:
        self._update_readouts()
        if self.app.link.connected:
            # Tk Scale emits an event for practically every pixel while it is
            # dragged.  Sending each intermediate value overflowed the ESP32
            # command stream (hundreds of CONFIGs in a few seconds).  Keep only
            # the final value after a short, imperceptible pause.
            if self._config_after_id is not None:
                self.app.root.after_cancel(self._config_after_id)
            self._config_after_id = self.app.root.after(
                CONFIG_DEBOUNCE_MS, self._send_pending_config
            )

    def _send_pending_config(self) -> None:
        self._config_after_id = None
        if self.app.link.connected:
            self.app.send(self.config_command(), log=False)

    def _cancel_pending_config(self) -> None:
        if self._config_after_id is not None:
            self.app.root.after_cancel(self._config_after_id)
            self._config_after_id = None

    def set_profile(self, speed: float, acceleration: float, smooth: int) -> None:
        self.speed_var.set(speed)
        self.accel_var.set(acceleration)
        self.smooth_var.set(smooth)
        self._setting_changed()

    def apply_driver_mode(self) -> None:
        if not self.app.link.connected:
            self.app.set_connection_status("Сначала подключи ESP32")
            return
        if not self.app.telemetry_supported:
            self.app.last_message_var.set(
                "Режим TMC не отправлен: снача нужна новая прошивка ESP32"
            )
            return
        if self.active:
            self.app.last_message_var.set(
                f"Сначала останови ось {self.index}, затем меняй режим драйвера"
            )
            return
        mode = DRIVER_MODE_COMMANDS[self.driver_mode_var.get()]
        try:
            transition_deg_s = max(1.0, min(10.0, float(self.transition_var.get())))
        except (tk.TclError, ValueError):
            transition_deg_s = 3.0
            self.transition_var.set(transition_deg_s)
        transition_pps = round(transition_deg_s * PULSES_PER_OUTPUT_DEGREE)
        if self.app.send(f"TMCMODE {self.index} {mode} {transition_pps}"):
            self.app.last_message_var.set(
                f"Ось {self.index}: запрос {mode}; переход гибрида {transition_deg_s:.1f}°/с"
            )

    @staticmethod
    def _integer(fields: dict[str, str], name: str, default: int = 0) -> int:
        try:
            return int(fields.get(name, str(default)), 0)
        except ValueError:
            return default

    def start(self, direction: int) -> None:
        if not self.app.link.connected:
            self.app.set_connection_status("Сначала подключи ESP32")
            return
        self._cancel_pending_config()
        self.app.send(self.config_command(), log=False)
        if self.app.send(f"JOG {self.index} {direction}"):
            self.active = True
            self.app.active_axes.add(self.index)

    def stop(self) -> None:
        if self.active:
            self.app.send(f"STOP {self.index}", log=False)
        self.active = False
        self.app.active_axes.discard(self.index)

    def update_status(self, fields: dict[str, str]) -> None:
        state = fields.get("state", "?")
        speed = fields.get("output_deg_s", "0")
        position = fields.get("position_deg_rel", "0")
        self.live_state.set(f"ESP32: {state}  ·  сейчас {speed} °/с  ·  относит. угол {position}°")

    def update_driver_status(self, fields: dict[str, str]) -> None:
        uart = fields.get("uart", "OFFLINE")
        if uart != "ONLINE":
            self.driver_state.set("UART: НЕТ СВЯЗИ — проверь питание 12 В и провода")
            self.driver_temperature.set("Температура кристалла: недоступна")
            self.driver_load.set("Нагрузка и токовая шкала: недоступны")
            self.driver_faults.set("Диагностика драйвера: недоступна")
            return

        actual_mode = fields.get("mode", "?")
        requested_mode = fields.get("requested_mode", "PASSIVE")
        verified = fields.get("config_verified", "0") == "1"
        verify_text = "настройка подтверждена" if verified else "только наблюдение"
        self.driver_state.set(
            f"UART ONLINE · TMC2209 {fields.get('version', '?')} · сейчас {actual_mode} · "
            f"запрос {requested_mode} · {verify_text}"
        )

        ot = self._integer(fields, "ot")
        otpw = self._integer(fields, "otpw")
        if ot:
            temperature = "АВАРИЙНЫЙ ПЕРЕГРЕВ — силовая часть отключена"
        elif self._integer(fields, "t157"):
            temperature = "не ниже 157°C — НЕМЕДЛЕННО ОСТАНОВИТЬ"
        elif self._integer(fields, "t150"):
            temperature = "не ниже 150°C — критически горячо"
        elif self._integer(fields, "t143"):
            temperature = "не ниже 143°C — критически горячо"
        elif self._integer(fields, "t120") or otpw:
            temperature = "не ниже 120°C — предупреждение"
        else:
            temperature = "ни один порог не достигнут (обычно <120°C)"
        self.driver_temperature.set(
            f"Температура кристалла драйвера: {temperature}; это не температура мотора"
        )

        standstill = self._integer(fields, "standstill") == 1
        cs_actual = fields.get("cs_actual", "?")
        pwm_sum = fields.get("pwm_scale_sum", "?")
        if standstill:
            load_text = "SG_RESULT недостоверен на стоянке"
        else:
            load_text = f"SG_RESULT={fields.get('sg_result', '?')} (больше = легче нагрузка)"
        self.driver_load.set(
            f"{load_text} · CS_ACTUAL={cs_actual}/31 · PWM_SCALE_SUM={pwm_sum}"
        )

        faults: list[str] = []
        if self._integer(fields, "short_a"):
            faults.append("короткое фазы A")
        if self._integer(fields, "short_b"):
            faults.append("короткое фазы B")
        gstat = self._integer(fields, "gstat")
        if gstat & 0b010:
            faults.append("DRV_ERR")
        if gstat & 0b100:
            faults.append("просадка charge-pump")
        if not standstill:
            if self._integer(fields, "open_a"):
                faults.append("возможный обрыв фазы A")
            if self._integer(fields, "open_b"):
                faults.append("возможный обрыв фазы B")
        elif self._integer(fields, "open_a") or self._integer(fields, "open_b"):
            faults.append("OPEN_LOAD на стоянке игнорируется")
        self.driver_faults.set(
            "Диагностика: " + (" · ".join(faults) if faults else "ошибок не обнаружено")
        )

    def update_driver_basic_status(self, fields: dict[str, str]) -> None:
        if fields.get("uart") == "ONLINE":
            self.driver_state.set(
                f"UART ONLINE · TMC2209 {fields.get('version', '?')} · ожидается новая прошивка"
            )
        else:
            self.driver_state.set("UART: НЕТ СВЯЗИ")
        self.driver_temperature.set("Расширенная телеметрия появится после перезаливки ESP32")
        self.driver_load.set("SG_RESULT и токовая шкала пока не считываются")
        self.driver_faults.set("Кнопки режима пока не применять")


class ArmControlPanel:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Роборука J1 + J2 — плавное быстрое управление")
        self.root.geometry("1240x940")
        self.root.minsize(1120, 850)
        self.root.configure(bg="#0f172a")

        self.logger = SessionLogger()
        self.incoming: queue.Queue[str] = queue.Queue()
        self.link = SerialLink(self.incoming)
        self.active_axes: set[int] = set()
        self.key_down: set[str] = set()
        self.closing = False
        self.telemetry_supported = True

        self.port_var = tk.StringVar(value="COM7")
        self.connection_var = tk.StringVar(value="ESP32 не подключена")
        self.last_message_var = tk.StringVar(value="Движение начнётся только при удержании синей кнопки.")
        self.log_path_var = tk.StringVar(
            value=f"Логи: {self.logger.raw_path.name} + {self.logger.csv_path.name}"
        )
        self.axes: list[AxisPanel] = []

        self._build_style()
        self._build_ui()
        self.refresh_ports()
        self._bind_controls()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._poll_incoming)
        self.root.after(120, self._heartbeat)
        self.root.after(500, self._status_poll)
        self.root.after(700, self.connect)

    def _build_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0f172a")
        style.configure("TLabelframe", background="#172033", foreground="#f8fafc")
        style.configure("TLabelframe.Label", background="#0f172a", foreground="#f8fafc", font=("Segoe UI Semibold", 16))
        style.configure("TLabel", background="#172033", foreground="#dbeafe", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#0f172a", foreground="#f8fafc", font=("Segoe UI Semibold", 21))
        style.configure("Sub.TLabel", background="#0f172a", foreground="#a5b4fc", font=("Segoe UI", 10))
        style.configure("Value.TLabel", background="#172033", foreground="#93c5fd", font=("Segoe UI Semibold", 10))
        style.configure("Live.TLabel", background="#172033", foreground="#86efac", font=("Segoe UI Semibold", 10))
        style.configure("Driver.TLabel", background="#172033", foreground="#fcd34d", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI Semibold", 10), padding=7)
        style.configure("TCheckbutton", background="#172033", foreground="#dbeafe")

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Роборука: нижний + верхний механизм", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="NEMA17 · 1/8 микрошаг · редуктор 1:71. Жёсткий предел обеих осей: 7258 имп/с (23°/с); рабочий запас: 20°/с. Esc — аварийный стоп.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(3, 14))

        connection = ttk.Frame(outer)
        connection.pack(fill="x", pady=(0, 14))
        ttk.Label(connection, text="COM-порт:", style="Sub.TLabel").pack(side="left")
        self.port_box = ttk.Combobox(connection, textvariable=self.port_var, width=11, state="readonly")
        self.port_box.pack(side="left", padx=(8, 6))
        ttk.Button(connection, text="Обновить", command=self.refresh_ports).pack(side="left")
        self.connect_button = ttk.Button(connection, text="Подключить", command=self.toggle_connection)
        self.connect_button.pack(side="left", padx=(6, 12))
        ttk.Label(connection, textvariable=self.connection_var, style="Sub.TLabel").pack(side="left")

        axis_holder = ttk.Frame(outer)
        axis_holder.pack(fill="both", expand=True)
        axis_holder.columnconfigure(0, weight=1)
        axis_holder.columnconfigure(1, weight=1)
        axis_holder.rowconfigure(0, weight=1)

        for column, defaults in enumerate(AXIS_DEFAULTS):
            panel = AxisPanel(self, axis_holder, defaults)
            panel.frame.grid(row=0, column=column, sticky="nsew", padx=(0, 7) if column == 0 else (7, 0))
            self.axes.append(panel)

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(14, 0))
        emergency = tk.Button(
            bottom,
            text="АВАРИЙНЫЙ СТОП  ·  ESC",
            font=("Segoe UI Black", 15),
            bg="#dc2626",
            fg="white",
            activebackground="#991b1b",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.emergency_stop,
            padx=22,
            pady=12,
        )
        emergency.pack(side="left")
        ttk.Button(bottom, text="Мягко остановить обе", command=self.smooth_stop_all).pack(side="left", padx=10)
        ttk.Label(bottom, textvariable=self.last_message_var, style="Sub.TLabel").pack(side="left", padx=(8, 0))

        log_bar = ttk.Frame(outer)
        log_bar.pack(fill="x", pady=(10, 0))
        ttk.Button(
            log_bar,
            text="⚠ ВИБРАЦИЯ / СРЫВ",
            command=lambda: self.mark_log("PROBLEM"),
        ).pack(side="left")
        ttk.Button(
            log_bar,
            text="РАБОТАЕТ ХОРОШО",
            command=lambda: self.mark_log("GOOD"),
        ).pack(side="left", padx=(7, 0))
        ttk.Button(log_bar, text="Открыть папку логов", command=self.open_log_folder).pack(
            side="left", padx=(7, 12)
        )
        ttk.Label(log_bar, textvariable=self.log_path_var, style="Sub.TLabel").pack(side="left")

    def _bind_controls(self) -> None:
        self.root.bind_all("<ButtonRelease-1>", self._global_mouse_release, add="+")
        key_map = {
            "Left": (0, -1),
            "Right": (0, 1),
            "Down": (1, -1),
            "Up": (1, 1),
        }
        for key, (axis, direction) in key_map.items():
            self.root.bind_all(
                f"<KeyPress-{key}>",
                lambda _event, k=key, a=axis, d=direction: self._key_press(k, a, d),
            )
            self.root.bind_all(
                f"<KeyRelease-{key}>",
                lambda _event, k=key, a=axis: self._key_release(k, a),
            )
        self.root.bind_all("<space>", lambda _event: self.smooth_stop_all())
        self.root.bind_all("<Escape>", lambda _event: self.emergency_stop())

    def refresh_ports(self) -> None:
        ports = [item.device for item in list_ports.comports()]
        self.port_box["values"] = ports
        if "COM7" in ports:
            self.port_var.set("COM7")
        elif ports and self.port_var.get() not in ports:
            self.port_var.set(ports[0])

    def set_connection_status(self, text: str) -> None:
        self.connection_var.set(text)

    def open_log_folder(self) -> None:
        os.startfile(str(LOG_DIRECTORY))

    def mark_log(self, label: str = "MARK") -> None:
        settings = []
        for axis in self.axes:
            settings.append(
                f"axis{axis.index}:speed_pps={axis.speed_pps},"
                f"accel_pps2={axis.accel_pps2},smooth={axis.smooth_var.get()},"
                f"active={1 if axis.active else 0}"
            )
        message = f"{label}; " + "; ".join(settings)
        self.logger.raw("MARK", message)
        self.logger.record("LOCAL", "MARK", message=message)
        self.last_message_var.set(
            f"Метка {label} записана вместе с текущими настройками обеих осей"
        )

    def connect(self) -> None:
        if self.link.connected:
            return
        port = self.port_var.get().strip()
        if not port:
            self.set_connection_status("COM-порт не найден")
            return
        try:
            self.link.connect(port)
            self.logger.raw("LOCAL", f"CONNECTED {port}")
            self.logger.record("LOCAL", "CONNECTED", message=port)
            self.set_connection_status(f"Подключено: {port}")
            self.connect_button.configure(text="Отключить")
            for axis in self.axes:
                self.send(axis.config_command(), log=False)
            self.send("STATUS", log=False)
        except Exception as exc:
            self.set_connection_status("Ошибка подключения")
            self.last_message_var.set(str(exc))

    def disconnect(self) -> None:
        if self.link.connected:
            self.link.send("ESTOP")
            time.sleep(0.03)
        self.link.disconnect()
        self.logger.raw("LOCAL", "DISCONNECTED")
        self.logger.record("LOCAL", "DISCONNECTED")
        self.active_axes.clear()
        for axis in self.axes:
            axis.active = False
        self.set_connection_status("ESP32 не подключена")
        self.connect_button.configure(text="Подключить")

    def toggle_connection(self) -> None:
        if self.link.connected:
            self.disconnect()
        else:
            self.connect()

    def send(self, command: str, log: bool = True, record: bool = True) -> bool:
        if record:
            self.logger.raw("TX", command)
            self.logger.record("TX", command.split(maxsplit=1)[0], message=command)
        if not self.link.send(command):
            self.set_connection_status("Нет связи с ESP32")
            return False
        if log:
            self.last_message_var.set(f"→ {command}")
        return True

    def smooth_stop_all(self) -> None:
        self.send("STOP ALL", log=False)
        self.active_axes.clear()
        for axis in self.axes:
            axis.active = False
        self.last_message_var.set("Обе оси плавно останавливаются")

    def emergency_stop(self) -> None:
        self.send("ESTOP", log=False)
        self.active_axes.clear()
        for axis in self.axes:
            axis.active = False
        self.last_message_var.set("АВАРИЙНЫЙ СТОП")

    def _global_mouse_release(self, _event: tk.Event) -> None:
        for axis in self.axes:
            axis.stop()

    def _key_press(self, key: str, axis_index: int, direction: int) -> None:
        if key not in self.key_down:
            self.key_down.add(key)
            self.axes[axis_index].start(direction)

    def _key_release(self, key: str, axis_index: int) -> None:
        self.key_down.discard(key)
        self.axes[axis_index].stop()

    def _heartbeat(self) -> None:
        if not self.closing:
            if self.active_axes:
                # Heartbeats are safety traffic, not diagnostic data.  Omitting
                # them from the files keeps logs useful without changing the
                # 600 ms firmware watchdog behaviour.
                self.send("PING", log=False, record=False)
            self.root.after(120, self._heartbeat)

    def _status_poll(self) -> None:
        if not self.closing:
            if self.link.connected:
                self.send("TELEMETRY" if self.telemetry_supported else "STATUS", log=False)
            self.root.after(TELEMETRY_PERIOD_MS, self._status_poll)

    def _poll_incoming(self) -> None:
        while True:
            try:
                line = self.incoming.get_nowait()
            except queue.Empty:
                break

            self.logger.raw("RX", line)

            if line.startswith("AXIS "):
                parts = line.split(maxsplit=2)
                try:
                    index = int(parts[1])
                except (IndexError, ValueError):
                    continue
                fields = dict(AXIS_RE.findall(parts[2] if len(parts) > 2 else ""))
                fields["axis"] = str(index)
                self.logger.record("RX", "AXIS", fields=fields, message=line)
                if 1 <= index <= len(self.axes):
                    self.axes[index - 1].update_status(fields)
            elif line.startswith("TMCDETAIL "):
                parts = line.split(maxsplit=2)
                try:
                    index = int(parts[1])
                except (IndexError, ValueError):
                    continue
                fields = dict(AXIS_RE.findall(parts[2] if len(parts) > 2 else ""))
                fields["axis"] = str(index)
                self.logger.record("RX", "TMCDETAIL", fields=fields, message=line)
                if 1 <= index <= len(self.axes):
                    self.axes[index - 1].update_driver_status(fields)
            elif line.startswith("TMC "):
                parts = line.split(maxsplit=2)
                try:
                    index = int(parts[1])
                except (IndexError, ValueError):
                    continue
                fields = dict(AXIS_RE.findall(parts[2] if len(parts) > 2 else ""))
                fields["axis"] = str(index)
                self.logger.record("RX", "TMC", fields=fields, message=line)
                if 1 <= index <= len(self.axes):
                    self.axes[index - 1].update_driver_basic_status(fields)
            elif line.startswith("OK TMCMODE"):
                fields = dict(AXIS_RE.findall(line))
                self.logger.record("RX", "TMCMODE_OK", fields=fields, message=line)
                self.last_message_var.set(f"ESP32 подтвердила режим драйвера: {line}")
            elif line.startswith("ESTOP WATCHDOG"):
                self.active_axes.clear()
                for axis in self.axes:
                    axis.active = False
                self.last_message_var.set("ESP32 остановила движение: потерян heartbeat")
            elif line.startswith("LINK_ERROR"):
                self.active_axes.clear()
                self.set_connection_status("Связь потеряна — watchdog остановит моторы")
                self.last_message_var.set(line)
            elif line.startswith("ERR"):
                self.logger.record("RX", "ERROR", message=line)
                if line == "ERR UNKNOWN_COMMAND" and self.telemetry_supported:
                    self.telemetry_supported = False
                    self.last_message_var.set(
                        "Показан совместимый режим; расширенная телеметрия требует перезаливки"
                    )
                else:
                    self.last_message_var.set(f"ESP32: {line}")

        if not self.closing:
            self.root.after(100, self._poll_incoming)

    def close(self) -> None:
        self.closing = True
        self.disconnect()
        self.logger.close()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    ArmControlPanel(window)
    window.mainloop()
