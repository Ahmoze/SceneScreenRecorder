# 🎬 Scene-Grade Screen Recorder
### *High-Fidelity Screen Capture Tool for Windows*

![Platform](https://img.shields.io/badge/Platform-Windows%20(Win32)-blue?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?style=for-the-badge&logo=python)
![FFmpeg](https://img.shields.io/badge/Backend-FFmpeg-green?style=for-the-badge&logo=ffmpeg)
![Author](https://img.shields.io/badge/Author-TripleSec-red?style=for-the-badge)

---

## 📖 O Projektu

**Scene-Grade Screen Recorder** je napredni alat za snimanje ekrana, razvijen specifično da reši probleme sa kojima se suočavaju korisnici na Windows operativnim sistemima sa visokim DPI skaliranjem (High-DPI scaling).

Većina snimača koristi "logičku" rezoluciju koju prijavljuje Windows (npr. 150% scale), što rezultira mutnim snimcima ili pogrešnim kropovanjem. Ovaj alat koristi **Win32 API** (`ctypes`) za detekciju **fizičkih piksela** monitora i direktno komunicira sa `gdigrab` baferom grafičke kartice.

Rezultat je snimak "pixel-perfect" oštrine, bez obzira na sistemska podešavanja skaliranja.

### 👤 Autor
Razvio i dizajnirao: **triplesec**

---

## ✨ Ključne Funkcionalnosti

### 🔧 Hardverska Preciznost
* **Win32 Physical Capture:** Koristi `EnumDisplayMonitors` da zaobiđe Windows scaling bagove i dobije tačne koordinate (`rect.left`, `rect.top`).
* **DPI Awareness V2:** Aplikacija forsira `SetProcessDpiAwarenessContext` (DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2), obezbeđujući kristalno čist GUI na 4K ekranima.

### 🎨 Modularni Dizajn & Teme
* **Custom Teme:** Dolazi sa dve ugrađene teme koje menjaju kompletnu paletu boja:
    * 🔴 **Crimson:** Tamna tema sa crvenim akcentima (Default).
    * 🟢 **Terminal Green:** "Matrix" estetika sa zelenim akcentima.
* **Pametni UI:** GUI elementi se prilagođavaju veličini prozora, a input polja imaju fiksnu visinu radi konzistentnosti.

### ⚡ Workflow
* **Globalne Prečice:** Kontrolišite snimanje iz bilo koje aplikacije ili igre.
* **System Tray:** Minimizujte aplikaciju u tray (kod sata) - ona nastavlja da radi u pozadini.
* **FFmpeg Backend:** Koristi `libx264` (ultrafast/veryfast preset) za minimalno opterećenje procesora.

### 🔊 Snimanje Sistemskog Zvuka (DirectShow / Stereo Mix)

Aplikacija podržava snimanje **sistemskog zvuka** koristeći **Stereo Mix** preko DirectShow interfejsa. Ovo je izabrano kao najstabilnije rešenje koje zaobilazi probleme sa WASAPI drajverima na određenim Windows konfiguracijama.

**⚠️ VAŽNO: Kako omogućiti snimanje zvuka?**
Da bi ova funkcija radila, morate jednokratno omogućiti "Stereo Mix" u Windows-u:
1. Otvorite **Control Panel > Sound** (ili kucajte "Change system sounds" u Start meniju).
2. Idite na karticu **Recording** (Snimanje).
3. Desni klik na prazno belo polje -> Štiklirajte **"Show Disabled Devices"**.
4. Pojaviće se **Stereo Mix**. Desni klik na njega -> **Enable** (Omogući).

Tehnologija:
* `-f dshow` (DirectShow)
* Input: `audio="Stereo Mix (Realtek(R) Audio)"`
* Radi paralelno sa `gdigrab` video capture-om.

U GUI-u postoji opcija:
**[ ] Snimaj sistemski zvuk** koja automatski aktivira ovaj režim.

---

## 🔬 Tehnički "Deep Dive" (Forenzika Koda)

Ovaj deo objašnjava specifična inženjerska rešenja primenjena u projektu.

### 1. Rešenje za `QSpinBox` na Windows 11 (The "White Box" Fix)
Na Windows 11, kombinacija PySide6 i `Fusion` stila često dovodi do grafičkih grešaka na `QSpinBox` kontrolama (strelice postaju bele kocke ili nestaju). CSS (`QSS`) rešenja su se pokazala nestabilnim.

**Naše rešenje (`SpinBoxArrowStyle`):**
Umesto stilizovanja putem CSS-a, kreirali smo klasu koja nasleđuje `QtWidgets.QProxyStyle`.
* Presrećemo `drawComplexControl` događaj.
* Tražimo od sistema da iscrta **samo** okvir i tekst (`SC_SpinBoxFrame`, `SC_SpinBoxEditField`).
* **Ručno iscrtavamo strelice** koristeći `QPainter` i vektorsku geometriju (trouglove).
* Boja strelica se dinamički uzima iz `QPalette.ButtonText`, što znači da strelice automatski menjaju boju kada korisnik promeni temu (iz Crvene u Zelenu).

### 2. Zašto `gdigrab` preko `dshow`?
Iako `dshow` (DirectShow) nudi neke prednosti, `gdigrab` omogućava preciznije definisanje `offset_x` i `offset_y` parametara bez potrebe za instalacijom dodatnih drajvera (poput *screen-capture-recorder*). Ovo čini aplikaciju portabilnom ("portable") – dovoljan je samo `ffmpeg.exe`.

### 3. Arhitektura
Projekat je refaktorisan iz jedne skripte u modularni paket:
* `hardware.py`: Izolovani Win32 API pozivi.
* `styling.py`: Sva logika vezana za izgled (QSS + QProxyStyle).
* `ffmpeg_ctrl.py`: Upravljanje `subprocess` pozivima i tredovima za čitanje logova.

---

## ⌨️ Komande i Prečice

| Prečica | Funkcija | Opis |
| :--- | :--- | :--- |
| **`HOME`** | **Pauza / Nastavi** | Privremeno pauzira snimanje (Pause) i nastavlja ga (Resume) u isti fajl. |
| **`END`** | **Stop & Save** | Zaustavlja snimanje, gasi FFmpeg proces i čuva fajl na disk. |

---

## 🛠️ Instalacija i Pokretanje

### 1. Sistemski Zahtevi
* **Windows 10 ili 11** (x64).
* **Python 3.10+**.
* **FFmpeg** (Mora biti u `System PATH`).
    * *Test:* Otvorite CMD i kucajte `ffmpeg -version`.

### 2. Instalacija
Klonirajte repozitorijum i instalirajte zavisnosti:

```bash
git clone https://github.com/Ahmoze/SceneScreenRecorder.git
cd SceneScreenRecorder
pip install -r requirements.txt
```

### 3. Pokretanje
Aplikacija se pokreće preko `main.py` fajla u korenu projekta:

```bash
python main.py
```

---

## 📂 Struktura Fajlova

```text
SceneScreenRecorder/
│
├── main.py                 # Entry Point (pokreće GUI i učitava stilove)
├── requirements.txt        # Zavisnosti (PySide6)
├── README.md               # Dokumentacija
│
└── modules/                # Core logika aplikacije
    ├── __init__.py
    ├── constants.py        # Globalne konstante i putanje
    ├── ffmpeg_ctrl.py      # FFmpeg proces menadžer
    ├── hardware.py         # Win32 API (Monitori, DPI, Hotkeys)
    ├── styling.py          # Teme i Custom SpinBox iscrtavanje
    └── main_window.py      # Glavni GUI prozor
```

---

## 📝 Licenca

Projekat je otvorenog koda (**MIT License**).
Dizajnirano sa ❤️ od strane **triplesec**.

> *"Pixel-perfect capture for a pixel-perfect world."*