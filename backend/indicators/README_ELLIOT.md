# Elliott Wave Indikator – Backend/Frontend-Integration

---

## 1. Funktion / Workflow

- **Der Elliott-Wave-Indikator läuft vollständig im Backend** (`/backend/indicators/elliott_wave.py`).
- Verarbeitet einen **OHLCV-Zeitreihen-DataFrame** (z. B. Bitget, Binance).
- Die Ausgabe ist eine **Wellen-Liste**:
    - **Start/Ende** (Index/Time)
    - **Wellen-Typ** (Impulse/Korrektur)
    - **Labels** (`1`–`5`, `a`–`c`)
    - **Koordinaten der Pivotpunkte**
    - **Fibonacci-Level** (optional)

---

## 2. Datenfluss / API-Design

- **Frontend** fragt per REST-API einen Endpunkt an (z. B. `/indicators/elliott_wave`), übergibt:
    - Symbol, Zeitintervall, ggf. Indikator-Parameter (`depth`)
    - Optional: Darstellungs-Settings (Farben, Linienart)
- **Backend** liefert:
    - Liste aller gefundenen Wellen
    - Für jede Welle: Start/Ende, Typ, Label, Pivot-Koordinaten, Fibo-Level

**Beispiel JSON-Response:**
```json
[
  {
    "wave_no": 1,
    "wave_type": "impulse",
    "labels": ["1", "2", "3", "4", "5"],
    "pivot_idx": [30, 35, 40, 45, 50],
    "pivot_price": [0.073, 0.078, 0.076, 0.081, 0.079],
    "fibos": {
      "0.382": 0.0751,
      "0.5": 0.076,
      "0.618": 0.0768,
      "0.786": 0.0780,
      "1.618": 0.0838
    }
  }
]
````

---

## 3. Visualisierung / Integration (Frontend)

* **Candles anzeigen:** Wie bisher (mit eurer Chart-Library, z. B. lightweight-charts).
* **Trendlinien einzeichnen:**

  * Mit `pivot_idx` (X) und `pivot_price` (Y) als **Linie** über die Candles legen.
  * Die `labels` jeweils an den Pivotpunkten als Text/Badge anzeigen (`1`, `2`, … `a`, `b`, `c`).
* **Fibonacci-Retracements:**

  * Für jede Welle, die Fibo-Level enthält:

    * Mit Start/Ende der Welle (`pivot_idx[0]` bis `pivot_idx[-1]`), für jeden `fibos`-Wert eine **horizontale Linie** auf dem Chart.
    * Fibo-Level als Label und/oder in Tooltip anzeigen.

**UI-Settings (empfohlen):**

* Sichtbarkeit der Elliott-Waves togglen (On/Off)
* Farbe/Style für Impuls- und Korrekturwellen einstellbar
* Fibo-Level ein/ausblendbar
* „Invertieren“ (Wellenrichtung) für Short/Long je nach User-Einstellung

---

## 4. Frontend-Pseudocode

```javascript
// Axios/Fetch: Elliott-Wave-Daten laden
const response = await axios.get('/indicators/elliott_wave?symbol=BTCUSDT&interval=1m&depth=8');
const elliottWaves = response.data;

elliottWaves.forEach(wave => {
  // Trendlinie: X = pivot_idx, Y = pivot_price
  chart.addLine(wave.pivot_idx, wave.pivot_price, { color: ..., style: ... });
  // Labels: an jeden Pivot-Index ein Label (wave.labels)
  wave.pivot_idx.forEach((idx, i) => {
    chart.addLabel(idx, wave.pivot_price[i], wave.labels[i]);
  });
  // Fibo-Levels: horizontale Linien zwischen Start/Ende
  Object.entries(wave.fibos).forEach(([level, price]) => {
    chart.addHLine(wave.pivot_idx[0], wave.pivot_idx[wave.pivot_idx.length - 1], price, { label: `Fibo ${level}` });
  });
});
```

---

## 5. Edge Cases & Hinweise

* **Keine Welle gefunden?** → Leeres Array, keine Anzeige.
* **Sehr kurze Wellen?** → Filter im Frontend, um Überladung zu vermeiden.
* **Performance:** Backend sendet nur **aktuelle, sichtbare Wellen** (z. B. letzte 50).
* **User-Settings:** Alle Indikator-Parameter (z. B. ZigZag-Depth, Farben) via Panel/UI einstellbar.

---

## 6. FAQ für das Frontend-Team

* **Wie hole ich die Daten?**

  * Über den Elliott-Wave-API-Endpunkt:
    `GET /indicators/elliott_wave?symbol=...&interval=...&depth=...`
* **Was mache ich mit den Pivot-Indizes?**

  * Verwende sie als X-Koordinaten, um Linien und Labels zu positionieren.
* **Wie kann ich nur bestimmte Wellen anzeigen?**

  * Filtere nach `wave_type` oder baue einen UI-Selector.

---

## TL;DR

Das Frontend bekommt eine **strukturierte Liste aller Elliott-Waves mit allen Pivotpunkten, Labels und Fibonacci-Levels**.
**Zeichnet diese exakt wie in TradingView als Overlay auf den Chart!**
