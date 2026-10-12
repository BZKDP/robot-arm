import queue
import re
import threading
import time
import tkinter as tk
from tkinter import ttk

import serial
from serial.tools import list_ports


STATE_RE = re.compile(r"(\w+)=([^\s]+)")


class SerialWorker:
    def __init__(self, on_line):
        self.on_line = on_line
        self.ser = None
        self.thread = None
        self.stop_flag = threading.Event()

    def ports(self):
        return [p.device for p in list_ports.comports()]

    def connected(self):
        return self.ser is not None and self.ser.is_open

    def connect(self, port, baud=115200):
        self.disconnect()
        self.stop_flag.clear()
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def disconnect(self):
        self.stop_flag.set()
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def send(self, text):
        if not self.connected():
            return
        if not text.endswith("\n"):
            text += "\n"
        self.ser.write(text.encode("ascii", errors="ignore"))

    def _read_loop(self):
        while not self.stop_flag.is_set() and self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self.on_line(line)
            except Exception as exc:
                self.on_line(f"MONITOR_ERROR {exc}")
                time.sleep(0.2)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Ручной тест сустава - ESP32 / TMC2209 / AS5600")
        self.lines = queue.Queue()
        self.worker = SerialWorker(self.lines.put)
        self.state = {}

        self.port_var = tk.StringVar()
        self.speed_var = tk.IntVar(value=500)
        self.goto_var = tk.StringVar(value="90")
        self.cmd_var = tk.StringVar()

        self._build()
        self.refresh_ports()
        self.root.after(50, self._pump)

    def _build(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        top = ttk.Frame(main)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="COM").grid(row=0, column=0, padx=(0, 6))
        self.port_combo = ttk.Combobox(top, textvariable=self.port_var, width=12, state="readonly")
        self.port_combo.grid(row=0, column=1, sticky="w")
        ttk.Button(top, text="Обновить", command=self.refresh_ports).grid(row=0, column=2, padx=4)
        self.conn_btn = ttk.Button(top, text="Подключить", command=self.toggle_connect)
        self.conn_btn.grid(row=0, column=3, padx=4)

        status = ttk.LabelFrame(main, text="Данные", padding=8)
        status.grid(row=1, column=0, sticky="ew", pady=8)
        for i in range(6):
            status.columnconfigure(i, weight=1)
        self.labels = {}
        for i, key in enumerate(["ok", "raw", "deg", "mag", "mode", "en", "sps", "max", "accel", "target", "inv"]):
            ttk.Label(status, text=key).grid(row=i // 3 * 2, column=i % 3 * 2, sticky="w")
            val = ttk.Label(status, text="-", font=("Segoe UI", 11, "bold"))
            val.grid(row=i // 3 * 2, column=i % 3 * 2 + 1, sticky="w", padx=(4, 18))
            self.labels[key] = val

        controls = ttk.LabelFrame(main, text="Мотор", padding=8)
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        for i in range(8):
            controls.columnconfigure(i, weight=1)

        ttk.Button(controls, text="Шаги ON", command=lambda: self.send("EN 1")).grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        ttk.Button(controls, text="Шаги OFF", command=lambda: self.send("EN 0")).grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        ttk.Button(controls, text="СТОП", command=self.stop).grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        ttk.Button(controls, text="Ноль", command=lambda: self.send("ZERO")).grid(row=0, column=3, padx=3, pady=3, sticky="ew")
        ttk.Button(controls, text="INV 0", command=lambda: self.send("INV 0")).grid(row=0, column=4, padx=3, pady=3, sticky="ew")
        ttk.Button(controls, text="INV 1", command=lambda: self.send("INV 1")).grid(row=0, column=5, padx=3, pady=3, sticky="ew")
        ttk.Button(controls, text="SCAN", command=lambda: self.send("SCAN")).grid(row=0, column=6, padx=3, pady=3, sticky="ew")
        ttk.Button(controls, text="STATUS", command=lambda: self.send("STATUS")).grid(row=0, column=7, padx=3, pady=3, sticky="ew")

        ttk.Label(controls, text="Скорость, шаг/с").grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        speed = ttk.Scale(controls, from_=0, to=50000, orient="horizontal", variable=self.speed_var)
        speed.grid(row=1, column=2, columnspan=4, sticky="ew", pady=(10, 0))
        self.speed_label = ttk.Label(controls, text="500")
        self.speed_label.grid(row=1, column=6, sticky="w", pady=(10, 0))
        speed_entry = ttk.Entry(controls, textvariable=self.speed_var, width=8)
        speed_entry.grid(row=1, column=7, sticky="ew", pady=(10, 0))
        speed_entry.bind("<Return>", lambda _e: self.set_speed(self.speed_var.get()))
        speed.configure(command=self.on_speed_change)

        jog_minus = ttk.Button(controls, text="Удерживать -")
        jog_minus.grid(row=2, column=0, columnspan=2, padx=3, pady=8, sticky="ew")
        jog_minus.bind("<ButtonPress-1>", lambda _e: self.jog(-1))
        jog_minus.bind("<ButtonRelease-1>", lambda _e: self.stop())

        jog_plus = ttk.Button(controls, text="Удерживать +")
        jog_plus.grid(row=2, column=2, columnspan=2, padx=3, pady=8, sticky="ew")
        jog_plus.bind("<ButtonPress-1>", lambda _e: self.jog(1))
        jog_plus.bind("<ButtonRelease-1>", lambda _e: self.stop())

        ttk.Label(controls, text="Угол").grid(row=2, column=4, sticky="e")
        ttk.Entry(controls, textvariable=self.goto_var, width=8).grid(row=2, column=5, padx=3, sticky="ew")
        ttk.Button(controls, text="GOTO", command=self.goto).grid(row=2, column=6, padx=3, sticky="ew")

        for i, preset in enumerate([100, 500, 1000, 3000, 8000, 15000, 30000, 50000]):
            ttk.Button(controls, text=str(preset), command=lambda v=preset: self.set_speed(v)).grid(
                row=3, column=i, padx=3, pady=(0, 6), sticky="ew"
            )

        ttk.Button(controls, text="Старт постоянно -", command=lambda: self.jog(-1)).grid(
            row=4, column=0, columnspan=3, padx=3, pady=(0, 3), sticky="ew"
        )
        ttk.Button(controls, text="Старт постоянно +", command=lambda: self.jog(1)).grid(
            row=4, column=3, columnspan=3, padx=3, pady=(0, 3), sticky="ew"
        )
        ttk.Button(controls, text="СТОП", command=self.stop).grid(
            row=4, column=6, columnspan=2, padx=3, pady=(0, 3), sticky="ew"
        )

        terminal = ttk.LabelFrame(main, text="Лог / команда", padding=8)
        terminal.grid(row=3, column=0, sticky="nsew")
        main.rowconfigure(3, weight=1)
        terminal.columnconfigure(0, weight=1)
        terminal.rowconfigure(0, weight=1)

        self.log = tk.Text(terminal, height=15, wrap="none")
        self.log.grid(row=0, column=0, columnspan=3, sticky="nsew")
        scroll = ttk.Scrollbar(terminal, command=self.log.yview)
        scroll.grid(row=0, column=3, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)

        entry = ttk.Entry(terminal, textvariable=self.cmd_var)
        entry.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        entry.bind("<Return>", lambda _e: self.send_cmd_entry())
        ttk.Button(terminal, text="Отправить", command=self.send_cmd_entry).grid(row=1, column=1, padx=4, pady=(8, 0))
        ttk.Button(terminal, text="Help", command=lambda: self.send("HELP")).grid(row=1, column=2, padx=4, pady=(8, 0))

    def refresh_ports(self):
        ports = self.worker.ports()
        self.port_combo["values"] = ports
        if "COM7" in ports:
            self.port_var.set("COM7")
        elif ports and self.port_var.get() not in ports:
            self.port_var.set(ports[0])

    def toggle_connect(self):
        if self.worker.connected():
            self.worker.disconnect()
            self.conn_btn.configure(text="Подключить")
            return
        port = self.port_var.get().strip()
        if not port:
            self.append_log("Pick a COM port first")
            return
        try:
            self.worker.connect(port)
            self.conn_btn.configure(text="Отключить")
            self.append_log(f"Подключено: {port}")
        except Exception as exc:
            self.append_log(f"Ошибка подключения: {exc}")

    def send(self, cmd):
        self.append_log(f"> {cmd}")
        self.worker.send(cmd)

    def set_speed(self, value):
        try:
            speed = int(float(value))
        except (TypeError, ValueError, tk.TclError):
            speed = 0
        speed = max(0, min(50000, speed))
        self.speed_var.set(speed)
        self.speed_label.configure(text=str(speed))

    def on_speed_change(self, _value):
        self.set_speed(self.speed_var.get())

    def jog(self, sign):
        speed = max(0, min(50000, int(self.speed_var.get())))
        if speed == 0:
            self.stop()
            return
        self.send("MAX 50000")
        self.send("ACCEL 25000")
        self.send("EN 1")
        self.send(f"JOG {sign * speed}")

    def stop(self):
        self.send("STOP")

    def goto(self):
        val = self.goto_var.get().strip().replace(",", ".")
        self.send(f"GOTO {val}")

    def send_cmd_entry(self):
        cmd = self.cmd_var.get().strip()
        if cmd:
            self.send(cmd)
            self.cmd_var.set("")

    def append_log(self, line):
        self.log.insert("end", line + "\n")
        self.log.see("end")

    def parse_state(self, line):
        if not line.startswith("STATE "):
            return
        self.state = dict(STATE_RE.findall(line))
        for key, label in self.labels.items():
            label.configure(text=self.state.get(key, "-"))

    def _pump(self):
        try:
            while True:
                line = self.lines.get_nowait()
                self.append_log(line)
                self.parse_state(line)
        except queue.Empty:
            pass
        self.root.after(50, self._pump)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("880x620")
    App(root)
    root.mainloop()
