import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

import serial
from serial.tools import list_ports


BAUD_RATE = 115200
DEFAULT_PORT = "COM7"
DEFAULT_SPEED = 80


class MotorPanel:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Роборука — тест двигателя 1")
        self.root.geometry("720x500")
        self.root.minsize(650, 450)
        self.root.configure(bg="#111827")

        self.serial_port: serial.Serial | None = None
        self.serial_lock = threading.Lock()
        self.messages: queue.Queue[str] = queue.Queue()
        self.motion: str | None = None
        self.key_down: set[str] = set()
        self.closing = False

        self.port_var = tk.StringVar(value=DEFAULT_PORT)
        self.speed_var = tk.IntVar(value=DEFAULT_SPEED)
        self.speed_text = tk.StringVar(value=f"{DEFAULT_SPEED} имп/с")
        self.status_var = tk.StringVar(value="Не подключено")
        self.invert_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._refresh_ports()

        self.root.bind_all("<KeyPress-Left>", self._left_key_down)
        self.root.bind_all("<KeyRelease-Left>", self._direction_key_up)
        self.root.bind_all("<KeyPress-Right>", self._right_key_down)
        self.root.bind_all("<KeyRelease-Right>", self._direction_key_up)
        self.root.bind_all("<space>", lambda _event: self.stop())
        self.root.bind_all("<ButtonRelease-1>", self._global_mouse_release, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.root.after(100, self._poll_messages)
        self.root.after(150, self._heartbeat)
        self.root.after(500, self.connect)

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#111827")
        style.configure("TLabel", background="#111827", foreground="#e5e7eb", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 20), foreground="#f9fafb")
        style.configure("Status.TLabel", font=("Segoe UI Semibold", 11))
        style.configure("TCheckbutton", background="#111827", foreground="#d1d5db", font=("Segoe UI", 10))
        style.configure("TCombobox", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI Semibold", 11), padding=8)

        outer = ttk.Frame(self.root, padding=24)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Управление двигателем 1", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Без концевиков: движение идёт только пока удерживается кнопка.").pack(
            anchor="w", pady=(4, 18)
        )

        connection = ttk.Frame(outer)
        connection.pack(fill="x")
        ttk.Label(connection, text="Порт:").pack(side="left")
        self.port_box = ttk.Combobox(connection, width=12, textvariable=self.port_var, state="readonly")
        self.port_box.pack(side="left", padx=(8, 8))
        ttk.Button(connection, text="Обновить", command=self._refresh_ports).pack(side="left")
        self.connect_button = ttk.Button(connection, text="Подключить", command=self.connect)
        self.connect_button.pack(side="left", padx=(8, 12))
        ttk.Label(connection, textvariable=self.status_var, style="Status.TLabel").pack(side="left")

        speed_frame = ttk.Frame(outer)
        speed_frame.pack(fill="x", pady=(28, 10))
        ttk.Label(speed_frame, text="Скорость STEP:").pack(anchor="w")
        speed_row = ttk.Frame(speed_frame)
        speed_row.pack(fill="x", pady=(6, 0))
        self.speed_scale = tk.Scale(
            speed_row,
            from_=20,
            to=2000,
            orient="horizontal",
            resolution=10,
            showvalue=False,
            variable=self.speed_var,
            command=self._speed_changed,
            bg="#111827",
            fg="#f9fafb",
            troughcolor="#374151",
            activebackground="#60a5fa",
            highlightthickness=0,
            bd=0,
        )
        self.speed_scale.pack(side="left", fill="x", expand=True)
        ttk.Label(speed_row, textvariable=self.speed_text, width=12).pack(side="left", padx=(14, 0))

        ttk.Checkbutton(
            outer,
            text="Инвертировать физические направления",
            variable=self.invert_var,
        ).pack(anchor="w", pady=(2, 18))

        buttons = ttk.Frame(outer)
        buttons.pack(fill="both", expand=True)

        self.left_button = tk.Button(
            buttons,
            text="◀  ВЛЕВО\nудерживать",
            font=("Segoe UI Semibold", 17),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        self.left_button.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.left_button.bind("<ButtonPress-1>", lambda _event: self.start("LEFT"))

        self.stop_button = tk.Button(
            buttons,
            text="STOP\nПРОБЕЛ",
            font=("Segoe UI Black", 17),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.stop,
        )
        self.stop_button.pack(side="left", fill="both", expand=True, padx=8)

        self.right_button = tk.Button(
            buttons,
            text="ВПРАВО  ▶\nудерживать",
            font=("Segoe UI Semibold", 17),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        self.right_button.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.right_button.bind("<ButtonPress-1>", lambda _event: self.start("RIGHT"))

        self.last_message_var = tk.StringVar(value="Прошивка не двигает мотор до команды.")
        ttk.Label(outer, textvariable=self.last_message_var).pack(anchor="w", pady=(18, 0))

    def _refresh_ports(self) -> None:
        ports = [item.device for item in list_ports.comports()]
        self.port_box["values"] = ports
        if self.port_var.get() not in ports and ports:
            self.port_var.set(ports[0])

    def connect(self) -> None:
        if self.serial_port and self.serial_port.is_open:
            self.disconnect()
            return

        port = self.port_var.get().strip()
        if not port:
            self.status_var.set("COM-порт не найден")
            return

        try:
            connection = serial.Serial(port, BAUD_RATE, timeout=0.1, write_timeout=0.5)
            time.sleep(1.2)
            connection.reset_input_buffer()
            self.serial_port = connection
            self.status_var.set(f"Подключено: {port}")
            self.connect_button.configure(text="Отключить")
            self._send(f"SPEED {self.speed_var.get()}")
            self._send("STATUS")
            threading.Thread(target=self._reader, daemon=True).start()
        except Exception as exc:
            self.serial_port = None
            self.status_var.set("Ошибка подключения")
            self.last_message_var.set(str(exc))

    def disconnect(self) -> None:
        self.stop()
        connection = self.serial_port
        self.serial_port = None
        if connection:
            try:
                connection.close()
            except Exception:
                pass
        self.status_var.set("Не подключено")
        self.connect_button.configure(text="Подключить")

    def _reader(self) -> None:
        connection = self.serial_port
        while connection is self.serial_port and connection and connection.is_open:
            try:
                line = connection.readline().decode("utf-8", "replace").strip()
                if line:
                    self.messages.put(line)
            except Exception as exc:
                self.messages.put(f"SERIAL ERROR: {exc}")
                break

    def _send(self, command: str) -> bool:
        connection = self.serial_port
        if not connection or not connection.is_open:
            self.status_var.set("Сначала подключи COM-порт")
            return False
        try:
            with self.serial_lock:
                connection.write((command + "\n").encode("ascii"))
                connection.flush()
            return True
        except Exception as exc:
            self.motion = None
            self.messages.put(f"SERIAL ERROR: {exc}")
            return False

    def _speed_changed(self, _value: str) -> None:
        speed = self.speed_var.get()
        self.speed_text.set(f"{speed} имп/с")
        if self.serial_port and self.serial_port.is_open:
            self._send(f"SPEED {speed}")

    def start(self, requested_direction: str) -> None:
        direction = requested_direction
        if self.invert_var.get():
            direction = "RIGHT" if requested_direction == "LEFT" else "LEFT"

        if not self._send(f"SPEED {self.speed_var.get()}"):
            return
        if self._send(direction):
            self.motion = direction
            self.last_message_var.set(f"Команда движения: {requested_direction}")

    def stop(self) -> None:
        self.motion = None
        self._send("STOP")
        self.last_message_var.set("Остановлено")

    def _global_mouse_release(self, _event: tk.Event) -> None:
        if self.motion is not None:
            self.stop()

    def _left_key_down(self, _event: tk.Event) -> None:
        if "Left" not in self.key_down:
            self.key_down.add("Left")
            self.start("LEFT")

    def _right_key_down(self, _event: tk.Event) -> None:
        if "Right" not in self.key_down:
            self.key_down.add("Right")
            self.start("RIGHT")

    def _direction_key_up(self, event: tk.Event) -> None:
        self.key_down.discard(event.keysym)
        if not self.key_down:
            self.stop()

    def _heartbeat(self) -> None:
        if not self.closing:
            if self.motion is not None:
                self._send("PING")
            self.root.after(150, self._heartbeat)

    def _poll_messages(self) -> None:
        while True:
            try:
                message = self.messages.get_nowait()
            except queue.Empty:
                break
            self.last_message_var.set(f"ESP32: {message}")
            if message.startswith("SERIAL ERROR"):
                self.motion = None
                self.status_var.set("Связь потеряна — watchdog остановит мотор")
        if not self.closing:
            self.root.after(100, self._poll_messages)

    def close(self) -> None:
        self.closing = True
        self.stop()
        time.sleep(0.05)
        self.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    MotorPanel(window)
    window.mainloop()
