## ws_frontend/README.md

```markdown
# ws_frontend

## Überblick

Dies ist das **Frontend-Repository** des WebSocket-Projekts.  
Die GUI basiert auf React, Vite und Tailwind und ist so modular gebaut, dass sie auch per Builder.io oder Bolt erweitert/gepflegt werden kann.

---

## Projektstruktur

```text
/frontend
  ├── public/              # Statische Dateien, UMD-Plugins, Icons
  ├── src/                 # Haupt-Source (React, Komponenten, Styles)
  ├── index.html           # Einstiegspunkt (Platzhalter-Container)
  ├── vite.config.ts       # Build-Konfiguration
  ├── .gitignore
  └── ... (weitere Komponenten)
````

---

## Setup

### **Lokal entwickeln**

```bash
npm install
npm run dev
# GUI läuft dann auf http://localhost:8080
```

### **Build für Production**

```bash
npm run build
# Output liegt im dist/-Ordner
```

---

## Deployment

* Die GUI kann als statisches Bundle (dist/) über CDN, S3, Nginx oder jedes beliebige Static-Hosting ausgeliefert werden.
* Die Kommunikation mit dem Backend erfolgt ausschließlich per HTTP(S)/WebSocket – **kein direkter Code-Zugriff auf Backend nötig!**

---

## Zusammenarbeit mit Backend

* Das Backend (API, WS, DB) ist **getrennt** und liegt im Repo [`ws_backend`](https://github.com/sawyerma/ws_backend).
* Konfiguration der Backend-Endpoints erfolgt in `.env`-Dateien oder via Build-Config (VITE\_WS\_URL, VITE\_API\_URL etc.).

---

## Wochenplan / Meilensteine

### **Woche 0 – Static Build & Grundstruktur**

* Projektstruktur, Static Hosting, Platzhalter-DIVs, UMD-Plugin-Vorbereitung

### **Woche 1 – Build/Dev-Setup & Hot-Reload**

* NPM, Vite, Tailwind, Plugins, Hot-Reload im Dev-Modus

### **Woche 2 – Chart-Plugin & WS-Integration**

* WebSocket-Anbindung, Dummy-Chart, API-Integration, Error Handling

### **Woche 3 – Plugins & Pattern/Signal-Module**

* Chart-Pattern- und Signal-Plugins, Settings-UI, weitere Panels

### **Woche 4+ – Dashboard, Testing, ML-Module**

* Integration mit Admin-Dashboard, End-to-End-Tests, ML-Anbindung, finale GUI-Funktionen

---

## Hinweise

* **Nur GUI!** – Das Backend ist in [`ws_backend`](https://github.com/sawyerma/ws_backend)
* Keine sensiblen Daten, Secrets oder API-Keys im Repo!
* Bei Fragen siehe Issues, Doku oder melde dich direkt.

---

## Kontakt / Mitwirken
→ [sawyerma@github.com](mailto:sawyerma@github.com)
