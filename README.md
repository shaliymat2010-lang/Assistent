# Desktop Assistent

Ein minimalistischer Desktop-Assistent für Windows mit nativer Tkinter-Benutzeroberfläche, asynchroner Spracherkennung und modularer Programmverwaltung.

## Architektur

Das gesamte Projekt ist modular und kompakt in zwei Kern-Dateien sowie einer JSON-Konfiguration aufgebaut:

```text
├── main.py          # Backend-Logik: ConfigManager, VoiceRecognizer, Assistant, Programme & Start
├── gui.py           # Benutzeroberfläche: AssistantGUI, Themes, Tab-Steuerung & Voice-Anbindung
├── programme.json   # Konfiguration für Farbschema und registrierte Programme
├── requirements.txt # Python-Abhängigkeiten (psutil, SpeechRecognition, PyAudio)
├── .gitignore       # Git-Ausschlussregeln
└── README.md        # Projektdokumentation
```

## Funktionen

- **Kompakte 2-Dateien-Architektur**:
  - `main.py`: Enthält `ConfigManager`, `VoiceRecognizer`, `AssistantResponse`, `Assistant` sowie die Anwendungsinitialisierung `main()`.
  - `gui.py`: Vollständige Benutzeroberfläche `AssistantGUI` ohne zirkuläre Abhängigkeiten, empfängt Module sauber über den Konstruktor.
- **Sprachsteuerung (Voice Input)**:
  - Vollständige asynchrone Spracherkennung im Hintergrund (`SpeechRecognition`, `PyAudio`).
  - Thread-sichere Benachrichtigung der Oberfläche via `root.after()`.
  - Automatische Anpassung an Umgebungsgeräusche (`adjust_for_ambient_noise`).
  - Visuelle Rückmeldung direkt am Mikrofon-Button (`🔴 Höre zu...`, `⏳ Verarbeite...`) sowie Status-Label.
  - Automatische Befehlsausführung bei Spracherkennung mit Anzeige `Du (Sprache): <Befehl>`.
- **Farbschemata (Themes)**:
  - Drei abgestimmte Themes: `Dunkel` (Catppuccin-inspiriert), `Hell` und `Nord`.
  - Dynamisches Umschalten in Echtzeit über die Einstellungen.
- **Standardbefehle**:
  - `browser öffnen` / `webseite öffnen` – Startet den Standardbrowser.
  - `browser schließen` – Beendet laufende Browser-Prozesse (Chrome, Edge, Firefox, Brave, Opera) mit `psutil`.
  - `rechner öffnen` / `taschenrechner` – Öffnet den Windows-Taschenrechner.
  - `rechner schließen` – Schließt aktive Rechner-Prozesse.
  - `uhrzeit` / `wie spät ist es` – Gibt die aktuelle Uhrzeit aus.
  - `datum` / `welcher tag ist heute` – Zeigt das aktuelle Datum an.
  - `hilfe` / `befehle` – Listet alle verfügbaren Standard- und benutzerdefinierten Befehle auf.
  - `beenden` / `schließen` – Beendet die Anwendung sauber.
- **Eigene Anwendungen verwalten (`programme.json`)**:
  - Beliebige Programme (`.exe`) im Tab *Einstellungen* registrieren.
  - Dateiauswahl über integrierten Datei-Explorer (*Durchsuchen...*).
  - Übersichtstabelle (`Treeview`) aller gespeicherten Programme.
  - Bearbeiten durch Doppelklick und Entfernen über *Ausgewählten Befehl löschen*.
  - Automatische Persistierung in `programme.json`.

## Voraussetzungen

- **Betriebssystem**: Windows 10 / 11
- **Python**: Version 3.8 oder höher
- **Hardware**: Mikrofon für die Spracheingabe

## Installation

1. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

2. Assistenten starten:
   ```bash
   python main.py
   ```

## Konfiguration (`programme.json`)

Die Konfigurationsdatei wird bei Bedarf automatisch erstellt und speichert das gewählte Theme sowie die benutzerdefinierten Programme:

```json
{
    "theme": "Dunkel",
    "programme": [
        {
            "befehl": "spotify",
            "name": "Spotify",
            "pfad": "spotify.exe"
        }
    ]
}
```

## Bedienung

### Texteingabe
Befehl im Eingabefeld eintippen und `Enter` drücken oder auf **Senden** klicken.

### Spracheingabe
1. Auf **🎤 Sprechen** klicken.
2. Der Button signalisiert Aufnahmebereitschaft (**🔴 Höre zu...**).
3. Deutschen Befehl sprechen (z. B. *„Wie spät ist es?“* oder *„Taschenrechner öffnen“*).
4. Nach kurzer Audioverarbeitung (**⏳ Verarbeite...**) wird der Befehl automatisch ausgeführt.

### Eigene Anwendungen hinzufügen
1. Zum Reiter **Einstellungen** wechseln.
2. Erkennungsbefehl und optionalen Namen eingeben.
3. Über **Durchsuchen...** die `.exe`-Datei auswählen.
4. Auf **Hinzufügen** klicken. Der Befehl ist sofort per Text und Sprache einsatzbereit.
