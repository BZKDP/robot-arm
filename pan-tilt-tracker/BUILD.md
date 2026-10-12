# Камера-трекер на pan-tilt (STS3215 + ESP32-CAM + ПК)

Голова из 2× STS3215 водит ESP32-CAM, **ПК** в реальном времени держит лицо/человека
в центре кадра (MediaPipe). «Ум» (что это / найди X) — опциональным слоем (VLM).

> Вариант с Raspberry Pi 5 как мозгом — в истории git/старом BUILD. Сейчас мозг = ПК.

## Архитектура (всё на ПК, без докупок)
```
[STS3215 pan, ID1]──шина 1Мбод──[STS3215 tilt, ID2]
        └──────────── ESP32 (мост) ──USB──► ПК (Windows)
                                            ├─ MediaPipe: ловит цель в кадре
                                            ├─ P-регулятор → углы pan/tilt
                                            └─ (опц.) VLM «найди/что это»
[ESP32-CAM]──WiFi MJPEG :81/stream──────────► ПК (OpenCV читает поток)
```
- **ESP32 (обычная 30-pin) = мост к сервам.** USB в ПК. `Serial`=линк к ПК,
  `Serial1` (1 Мбод)=шина серв. Библиотека SCServo сама гасит эхо полудуплекса.
  - **Почему не Arduino Uno/Nano:** у них 1 аппаратный UART, занятый USB; на 1 Мбод
    полудуплекс нужен 2-й UART, а SoftwareSerial столько не тянет (~57600 потолок).
    ESP32 (3 UART, 3.3 В без level-shifter) — правильный инструмент, уже есть.
- **ПК (быстрый контур, ~30 fps):** OpenCV+MediaPipe ловит цель → P-регулятор →
  шлёт `pan tilt` в ESP32 по COM-порту. Слежение без задержек.
- **ESP32-CAM** = беспроводной видеопоток MJPEG `http://<ip>:81/stream`.
- **Умный слой (по запросу):** ПК шлёт кадр в VLM (локально Ollama на мини-ПК
  OLLAMA_HOST → `ollama pull qwen2.5vl:7b`, или облачный) — «где/что». Не каждый кадр.

## Что напечатано (5 деталей из 3MF, печать без поддержек)
Цепочка снизу вверх: **стол → base → pan-серва → скоба → tilt-серва → площадка → камера**
| Деталь | Роль |
|---|---|
| `base_link-print` | основание, на «стакан» снизу садится **pan-серва** (ось рысканья) |
| `pan_tilt_bracket-side` | П-скоба на роге pan; в «вилке» зажата **tilt-серва** (ось наклона) |
| `payload_link-flat` | площадка на роге tilt, несёт корпус камеры |
| `espcam-case-front` | крышка корпуса камеры (отверстие под объектив) |
| `espcam-case-back-mount2` | зад корпуса ESP32-CAM, крепится к payload_link |

## Питание (всё в наличии)
- Источник: блок **12 В 3 А** (бочонок) → снять 12 В адаптером бочонок→винт-клеммы.
- Понижайка: **LM2596 DC-DC** 12 В → **7.4 В** (вход IN, выход OUT по стрелке/надписям).
  Провода ПАЯТЬ напрямую в отверстия (без гребёнки).
- 🔴 НАСТРОИТЬ ДО ПОДКЛЮЧЕНИЯ СЕРВ: запитать только IN от 12 В, мультиметром на OUT
  крутить синий многооборотный винт до **7.4 В** (7.2–7.5 ок), и только потом паять OUT→сервы.
- STS3215 (7.4 В версия!) рабочее **6–7.4 В**. 12 В напрямую = сжечь. 5 В = слабо + ребут.
- LM2596 ~2 А пост./3 А пик — для лёгкой головы хватает (сервы не стопорятся).
- **ОБЩАЯ земля** ESP32 ↔ OUT− LM2596 ↔ сервы ↔ GND USB. НЕ питать сервы от пинов платы.

## Полудуплекс своими руками (резистор ~1 кОм, без фирменной платы)
Разъём STS3215 = 3 провода: белый=Signal, красный=VIN, чёрный=GND.
На 1 Мбод оптимум ~1 кОм (10 кОм подтормаживает фронт). Из имеющихся 220 Ом:
**5× 220 Ом последовательно ≈ 1.1 кОм.**
```
ESP32 GPIO16 (RX2) ────────────────────┬──→ белый (Signal)   ← RX напрямую
ESP32 GPIO17 (TX2) ──[ ~1 кОм ]─────────┘                     ← TX через резистор
ESP32 GND ───────────── OUT− LM2596 ───────→ чёрный (GND)     (ОБЩАЯ земля!)
LM2596 OUT+ (7.4 В) ───────────────────────→ красный (VIN)
```
- RX2 — напрямую на Signal (чистый приём). TX2 — через ~1 кОм на Signal.
- Узел Signal удобно сделать на отдельном WAGO: в него белый провод сервы +
  2 медных (один → столбик ≈1кОм → G17, второй → напрямую G16). Всего 3 WAGO:
  +7.4В, GND (общая земля), Signal. Схема узла: signal_junction.svg.
- Две сервы — насквозь бел-бел/красн-красн/чёрн-чёрн (daisy-chain), MCU к первой.
- Референс: github.com/sepastian/ESP32_ST3215 (ESP32 без фирменной платы).

## Прошивка серв (один раз): задать ID и центр
Сервы приходят с ID 1. Нужно: pan=ID 1, tilt=ID 2, обе baud 1 000 000, центр 2048.
1. Подключить ТОЛЬКО будущую tilt-серву, залить «смена ID» скетч (ниже) → ID 1→2.
2. Обе по очереди выставить в позицию 2048 (центр) до сборки.

```cpp
// Скетч смены ID: подключи ТОЛЬКО одну серву (текущий ID 1)
#include <SCServo.h>
SMS_STS st;
void setup(){
  Serial1.begin(1000000, SERIAL_8N1, 16, 17);
  st.pSerial = &Serial1; delay(500);
  st.unLockEprom(1);
  st.writeByte(1, SMS_STS_ID, 2);   // 1 → 2
  st.LockEprom(2);
}
void loop(){}
```

## Прошивка ESP32-моста (Arduino IDE, плата = ESP32 Dev Module)
Поставить либу **SCServo** (Feetech). Принимает `pan tilt\n` от ПК, отдаёт позиции.
```cpp
#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17
void setup(){
  Serial.begin(115200);                              // линк к ПК (COM)
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);  // шина серв (10к резистор!)
  st.pSerial = &Serial1;
}
void loop(){
  if (Serial.available()){
    int pan  = Serial.parseInt();
    int tilt = Serial.parseInt();
    st.WritePosEx(1, constrain(pan ,800,3300), 2000, 50);
    st.WritePosEx(2, constrain(tilt,800,3300), 2000, 50);
    // обратная связь: st.ReadPos(1) / st.ReadPos(2)  ← STS3215 отдаёт позицию всегда
  }
}
```

## Прошивка ESP32-CAM (камера)
Arduino IDE, плата **AI-Thinker ESP32-CAM**, пример `CameraWebServer`
(вписать SSID/пароль WiFi). Прошивать через плату-программатор ESP32-CAM-MB (USB).
Поток MJPEG: `http://<ip-esp32cam>:81/stream`. Узнать IP в Serial Monitor после старта.

## Софт на ПК (Windows, Python 3.10–3.12)
```powershell
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install opencv-python mediapipe pyserial requests
```
COM-порт ESP32-моста смотреть в Диспетчере устройств (напр. COM5).

### Связь ПК → ESP32 (мост)
```python
import serial
esp = serial.Serial('COM5', 115200, timeout=0.1)   # свой COM!
def move(pan, tilt):                                 # целевые позиции 800..3300
    esp.write(f"{int(pan)} {int(tilt)}\n".encode())
```

### Быстрый контур слежения (MediaPipe + P-регулятор)
```python
import cv2, mediapipe as mp, serial

esp = serial.Serial('COM5', 115200, timeout=0.1)
def move(pan, tilt): esp.write(f"{int(pan)} {int(tilt)}\n".encode())

cap = cv2.VideoCapture('http://192.168.1.XX:81/stream')   # IP ESP32-CAM
det = mp.solutions.face_detection.FaceDetection(model_selection=0,
                                                min_detection_confidence=0.5)
pan_pos, tilt_pos = 2048, 2048
Kp   = 1.2          # больше = резче, меньше = плавнее
DEAD = 0.04         # мёртвая зона в центре, чтобы не дрожала

while True:
    ok, frame = cap.read()
    if not ok: continue
    h, w = frame.shape[:2]
    res = det.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if res.detections:
        b = res.detections[0].location_data.relative_bounding_box
        cx, cy = b.xmin + b.width/2, b.ymin + b.height/2   # 0..1
        ex, ey = cx - 0.5, cy - 0.5                         # ошибка от центра
        if abs(ex) > DEAD: pan_pos  -= Kp * ex * (w/2)      # знак pan под свою сборку
        if abs(ey) > DEAD: tilt_pos += Kp * ey * (h/2)      # знак tilt под свою сборку
        pan_pos  = max(800, min(3300, pan_pos))
        tilt_pos = max(800, min(3300, tilt_pos))
        move(pan_pos, tilt_pos)
    cv2.imshow('track', frame)
    if cv2.waitKey(1) == 27: break
```

### Умный слой (опц.): VLM выбирает/называет цель — не каждый кадр
```python
import requests, base64, cv2
def ask_vlm(frame, prompt):
    _, jpg = cv2.imencode('.jpg', frame)
    b64 = base64.b64encode(jpg).decode()
    r = requests.post('http://OLLAMA_HOST:11434/api/generate', json={
        'model':'qwen2.5vl:7b', 'prompt':prompt, 'images':[b64], 'stream':False},
        timeout=30)
    return r.json()['response']
# для наведения проси «дай bbox цели в формате x,y,w,h 0..1»
```

## Порядок работы
1. ✅ Печать 5 деталей (в процессе).
2. Сменить ID tilt-сервы на 2, обе в центр 2048.
3. Собрать pan-tilt, прикрутить ESP32-CAM в корпус на payload.
4. Спаять полудуплекс (10к), подключить: шину серв + 7.4 В БП + USB-мост в ПК.
5. Прошить ESP32-CAM (CameraWebServer), узнать IP.
6. Поднять контур слежения на ПК, подобрать Kp и знаки осей.
7. (Опц.) прикрутить VLM-слой для «найди X / кто это».
