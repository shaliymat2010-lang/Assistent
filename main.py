import datetime
import json
import os
import re
import subprocess
import threading
from typing import Any, Callable, Dict, List, NamedTuple, Optional
import webbrowser

import psutil
import speech_recognition as sr

from gui import AssistantGUI


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "programme.json")
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        default_config: Dict[str, Any] = {
            "theme": "Dunkel",
            "programme": [
                {"befehl": "spotify", "name": "Spotify", "pfad": "spotify.exe"}
            ],
        }
        if not os.path.exists(self.config_path):
            self.config = default_config
            self.save_config()
            return self.config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception:
            self.config = default_config
            self.save_config()
            return self.config

        if "theme" not in self.config:
            self.config["theme"] = "Dunkel"
        if "programme" not in self.config:
            self.config["programme"] = self.config.get("custom_commands", default_config["programme"])
        return self.config

    def save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_theme(self) -> str:
        return self.config.get("theme", "Dunkel")

    def set_theme(self, theme_name: str) -> bool:
        if theme_name in self.get_available_themes():
            self.config["theme"] = theme_name
            self.save_config()
            return True
        return False

    def get_available_themes(self) -> List[str]:
        return ["Dunkel", "Hell", "Nord"]

    def get_programme(self) -> List[Dict[str, str]]:
        return self.config.get("programme", [])

    get_custom_commands = get_programme

    def add_programme(self, befehl: str, pfad: str, name: str = "") -> bool:
        befehl_clean = befehl.strip().lower()
        pfad_clean = pfad.strip()
        if not befehl_clean or not pfad_clean:
            return False

        display_name = name.strip() or befehl_clean.capitalize()
        programme = self.get_programme()

        for item in programme:
            if item.get("befehl", "").strip().lower() == befehl_clean:
                item["name"] = display_name
                item["pfad"] = pfad_clean
                self.save_config()
                return True

        programme.append({
            "befehl": befehl_clean,
            "name": display_name,
            "pfad": pfad_clean,
        })
        self.config["programme"] = programme
        self.save_config()
        return True

    add_custom_command = add_programme

    def remove_programme(self, befehl: str) -> bool:
        befehl_clean = befehl.strip().lower()
        programme = self.get_programme()
        vorher = len(programme)
        programme = [p for p in programme if p.get("befehl", "").strip().lower() != befehl_clean]
        if len(programme) < vorher:
            self.config["programme"] = programme
            self.save_config()
            return True
        return False

    remove_custom_command = remove_programme


class VoiceRecognizer:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self.is_listening: bool = False
        self._lock = threading.Lock()

    def listen_once(
        self,
        on_success: Callable[[str], None],
        on_status: Callable[[str], None],
        on_error: Callable[[str], None],
        language: str = "de-DE",
    ) -> None:
        with self._lock:
            if self.is_listening:
                return
            self.is_listening = True

        def _worker() -> None:
            try:
                try:
                    mic = sr.Microphone()
                except Exception:
                    on_error("Kein funktionierendes Mikrofon gefunden.")
                    return

                with mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                    on_status("Höre zu...")
                    audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=12)

                on_status("Verarbeite Audio...")
                text = self.recognizer.recognize_google(audio, language=language)
                if text and text.strip():
                    on_success(text.strip())
                else:
                    on_error("Keine Sprache erkannt oder nicht verstanden.")
            except sr.WaitTimeoutError:
                on_error("Keine Sprache erkannt (Zeitüberschreitung).")
            except sr.UnknownValueError:
                on_error("Keine Sprache erkannt oder nicht verstanden.")
            except sr.RequestError:
                on_error("Verbindungsfehler zum Spracherkennungsdienst.")
            except OSError:
                on_error("Mikrofon nicht erreichbar oder Zugriff verweigert.")
            except Exception as exc:
                on_error(f"Fehler bei der Spracherkennung: {exc}")
            finally:
                with self._lock:
                    self.is_listening = False

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()


class AssistantResponse(NamedTuple):
    erfolg: bool
    antwort_text: str
    aktion: Optional[str] = None


class Assistant:
    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        self.config_manager = config_manager or ConfigManager()

    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        return " ".join(text.split())

    def process_command(self, raw_input: str) -> AssistantResponse:
        norm = self.normalize_text(raw_input)
        if not norm:
            return AssistantResponse(False, "Keine Eingabe erkannt.", None)

        if norm in ("beenden", "schließen", "programm beenden", "exit", "quit", "tschüss"):
            return AssistantResponse(True, "Auf Wiedersehen!", "exit")

        if norm in ("browser öffnen", "webseite öffnen", "internet öffnen", "browser starten"):
            webbrowser.open("https://www.google.com")
            return AssistantResponse(True, "Webbrowser wurde geöffnet.", "browser_open")

        if norm in ("browser schließen", "browser beenden"):
            killed = self._kill_processes(["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"])
            if killed > 0:
                return AssistantResponse(True, f"Browser geschlossen ({killed} Prozess(e) beendet).", "browser_close")
            return AssistantResponse(False, "Keine aktiven Browser-Prozesse gefunden.", "browser_close")

        if norm in ("rechner öffnen", "taschenrechner", "taschenrechner öffnen", "rechner starten"):
            try:
                subprocess.Popen("calc.exe", shell=True)
                return AssistantResponse(True, "Taschenrechner wurde geöffnet.", "calc_open")
            except Exception as exc:
                return AssistantResponse(False, f"Fehler beim Öffnen des Rechners: {exc}", "calc_open")

        if norm in ("rechner schließen", "taschenrechner schließen", "rechner beenden"):
            killed = self._kill_processes(["calc.exe", "CalculatorApp.exe", "Calculator.exe"])
            if killed > 0:
                return AssistantResponse(True, f"Taschenrechner geschlossen ({killed} Prozess(e) beendet).", "calc_close")
            return AssistantResponse(False, "Keine aktiven Rechner-Prozesse gefunden.", "calc_close")

        if norm in ("uhrzeit", "wie spät ist es", "wie spät", "aktuelle uhrzeit"):
            zeit = datetime.datetime.now().strftime("%H:%M")
            return AssistantResponse(True, f"Es ist {zeit} Uhr.", "time")

        if norm in ("datum", "welcher tag ist heute", "welches datum haben wir", "welcher tag"):
            datum = datetime.datetime.now().strftime("%d.%m.%Y")
            return AssistantResponse(True, f"Heute ist der {datum}.", "date")

        if norm in ("hilfe", "befehle", "hilfe anzeigen", "was kannst du"):
            return AssistantResponse(True, self._get_help_text(), "help")

        custom_res = self._check_custom_commands(norm)
        if custom_res:
            return custom_res

        return AssistantResponse(False, "Befehl nicht erkannt. Tippe 'hilfe' für eine Liste der Befehle.", None)

    def _check_custom_commands(self, norm: str) -> Optional[AssistantResponse]:
        programme = self.config_manager.get_programme()
        words = norm.split()
        for cmd in programme:
            trigger = self.normalize_text(cmd.get("befehl", ""))
            name = cmd.get("name", trigger)
            pfad = cmd.get("pfad", "")
            if not trigger:
                continue

            if norm == trigger or trigger in words or f"{trigger} öffnen" in norm or f"{trigger} starten" in norm:
                try:
                    subprocess.Popen(pfad, shell=True)
                    return AssistantResponse(True, f"'{name}' wurde gestartet.", f"custom_{trigger}")
                except Exception as exc:
                    return AssistantResponse(False, f"Fehler beim Starten von '{name}': {exc}", f"custom_{trigger}")
        return None

    def _kill_processes(self, process_names: List[str]) -> int:
        killed = 0
        names_lower = {p.lower() for p in process_names}
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() in names_lower:
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return killed

    def _get_help_text(self) -> str:
        lines = [
            "Verfügbare Befehle:",
            "• 'browser öffnen' - Öffnet den Standard-Browser",
            "• 'browser schließen' - Schließt Browser-Prozesse",
            "• 'rechner öffnen' / 'taschenrechner' - Öffnet den Taschenrechner",
            "• 'rechner schließen' - Schließt den Taschenrechner",
            "• 'uhrzeit' / 'wie spät ist es' - Zeigt die aktuelle Uhrzeit",
            "• 'datum' / 'welcher tag ist heute' - Zeigt das aktuelle Datum",
            "• 'hilfe' / 'befehle' - Zeigt diese Hilfe",
            "• 'beenden' / 'schließen' - Beendet den Assistenten",
        ]
        programme = self.config_manager.get_programme()
        if programme:
            lines.append("\nBenutzerdefinierte Befehle:")
            for c in programme:
                lines.append(f"• '{c.get('befehl')}' - Startet {c.get('name')}")
        return "\n".join(lines)


def main() -> None:
    config_manager = ConfigManager()
    assistant = Assistant(config_manager=config_manager)
    voice_recognizer = VoiceRecognizer()
    gui = AssistantGUI(
        assistant=assistant,
        config_manager=config_manager,
        voice_recognizer=voice_recognizer,
    )
    gui.run()


if __name__ == "__main__":
    main()
