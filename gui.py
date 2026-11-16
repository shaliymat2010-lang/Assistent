import datetime
import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Any, Dict, List, Optional

THEMES: Dict[str, Dict[str, str]] = {
    "Dunkel": {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "accent": "#89b4fa",
        "input_bg": "#313244",
        "input_fg": "#cdd6f4",
        "button_bg": "#45475a",
        "button_fg": "#ffffff",
        "bot": "#a6e3a1",
        "user": "#89b4fa",
        "error": "#f38ba8",
        "muted": "#9399b2",
        "border": "#45475a",
        "accent_fg": "#11111b",
    },
    "Hell": {
        "bg": "#eff1f5",
        "fg": "#4c4f69",
        "accent": "#1e66f5",
        "input_bg": "#e6e9ef",
        "input_fg": "#4c4f69",
        "button_bg": "#dce0e8",
        "button_fg": "#4c4f69",
        "bot": "#40a02b",
        "user": "#1e66f5",
        "error": "#d20f39",
        "muted": "#7c7f93",
        "border": "#ccd0da",
        "accent_fg": "#ffffff",
    },
    "Nord": {
        "bg": "#2e3440",
        "fg": "#eceff4",
        "accent": "#88c0d0",
        "input_bg": "#3b4252",
        "input_fg": "#eceff4",
        "button_bg": "#434c5e",
        "button_fg": "#eceff4",
        "bot": "#a3be8c",
        "user": "#88c0d0",
        "error": "#bf616a",
        "muted": "#d8dee9",
        "border": "#4c566a",
        "accent_fg": "#2e3440",
    },
}


class AssistantGUI:
    def __init__(
        self,
        assistant: Optional[Any] = None,
        config_manager: Optional[Any] = None,
        voice_recognizer: Optional[Any] = None,
        root: Optional[tk.Tk] = None,
    ) -> None:
        self.assistant = assistant
        self.config_manager = config_manager
        self.voice_recognizer = voice_recognizer
        self.root = root or tk.Tk()

        self.root.title("Desktop Assistent")
        self.root.minsize(680, 520)

        width = 760
        height = 580
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.placeholder_text = "Befehl eingeben..."
        self.placeholder_active = True

        self._frames: List[tk.Frame] = []
        self._labels: List[tk.Label] = []
        self._headers: List[tk.Label] = []
        self._muted_labels: List[tk.Label] = []
        self._entries: List[tk.Entry] = []
        self._primary_buttons: List[tk.Button] = []
        self._secondary_buttons: List[tk.Button] = []

        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")

        initial_theme = "Dunkel"
        if self.config_manager and hasattr(self.config_manager, "get_theme"):
            initial_theme = self.config_manager.get_theme()
        self.current_theme = initial_theme
        self.current_colors: Dict[str, str] = {}

        self._build_ui()
        self.apply_theme(self.current_theme)
        self.refresh_command_list()
        self._show_welcome()

    def _build_ui(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_assistant = tk.Frame(self.notebook)
        self.tab_settings = tk.Frame(self.notebook)
        self._frames.extend([self.tab_assistant, self.tab_settings])

        self.notebook.add(self.tab_assistant, text="Assistent")
        self.notebook.add(self.tab_settings, text="Einstellungen")

        self._build_assistant_tab()
        self._build_settings_tab()

    def _build_assistant_tab(self) -> None:
        content_frame = tk.Frame(self.tab_assistant, padx=16, pady=16)
        content_frame.pack(fill="both", expand=True)
        self._frames.append(content_frame)

        bottom_box = tk.Frame(content_frame)
        bottom_box.pack(fill="x", side="bottom")
        self._frames.append(bottom_box)

        input_frame = tk.Frame(bottom_box)
        input_frame.pack(fill="x")
        self._frames.append(input_frame)

        self.btn_send = tk.Button(
            input_frame,
            text="Senden",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=18,
            pady=6,
            cursor="hand2",
            command=self.send_command,
        )
        self.btn_send.pack(side="right")
        self._primary_buttons.append(self.btn_send)

        self.btn_voice = tk.Button(
            input_frame,
            text="🎤 Sprechen",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.start_voice_input,
        )
        self.btn_voice.pack(side="right", padx=(0, 8))
        self._secondary_buttons.append(self.btn_voice)

        self.entry_input = tk.Entry(
            input_frame,
            font=("Segoe UI", 10),
            relief="flat",
            highlightthickness=1,
        )
        self.entry_input.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self._entries.append(self.entry_input)

        self.entry_input.insert(0, self.placeholder_text)
        self.entry_input.bind("<FocusIn>", self._on_entry_focus_in)
        self.entry_input.bind("<FocusOut>", self._on_entry_focus_out)
        self.entry_input.bind("<Return>", lambda event: self.send_command())
        self.entry_input.bind("<KP_Enter>", lambda event: self.send_command())

        self.lbl_voice_status = tk.Label(
            bottom_box,
            text="",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_voice_status.pack(fill="x", pady=(4, 0))
        self._muted_labels.append(self.lbl_voice_status)

        chat_frame = tk.Frame(content_frame)
        chat_frame.pack(fill="both", expand=True, pady=(0, 10))
        self._frames.append(chat_frame)

        self.chat_text = tk.Text(
            chat_frame,
            wrap="word",
            font=("Segoe UI", 10),
            relief="flat",
            padx=14,
            pady=14,
            highlightthickness=1,
            state="disabled",
            cursor="arrow",
        )
        self.chat_scroll = ttk.Scrollbar(
            chat_frame,
            orient="vertical",
            command=self.chat_text.yview,
        )
        self.chat_text.configure(yscrollcommand=self.chat_scroll.set)

        self.chat_scroll.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)

    def _build_settings_tab(self) -> None:
        content_frame = tk.Frame(self.tab_settings, padx=20, pady=16)
        content_frame.pack(fill="both", expand=True)
        self._frames.append(content_frame)

        theme_header = tk.Label(
            content_frame,
            text="Erscheinungsbild",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        theme_header.pack(fill="x", pady=(0, 6))
        self._headers.append(theme_header)

        theme_row = tk.Frame(content_frame)
        theme_row.pack(fill="x", pady=(0, 16))
        self._frames.append(theme_row)

        lbl_theme = tk.Label(theme_row, text="Farbschema:", font=("Segoe UI", 9))
        lbl_theme.pack(side="left", padx=(0, 12))
        self._labels.append(lbl_theme)

        themes = list(THEMES.keys())
        self.combo_theme = ttk.Combobox(
            theme_row,
            values=themes,
            state="readonly",
            font=("Segoe UI", 9),
            width=18,
        )
        if self.current_theme in themes:
            self.combo_theme.set(self.current_theme)
        elif themes:
            self.combo_theme.current(0)
        self.combo_theme.pack(side="left")
        self.combo_theme.bind("<<ComboboxSelected>>", self._on_theme_changed)

        add_header = tk.Label(
            content_frame,
            text="Eigene Anwendung hinzufügen",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        add_header.pack(fill="x", pady=(0, 8))
        self._headers.append(add_header)

        form_frame = tk.Frame(content_frame)
        form_frame.pack(fill="x", pady=(0, 16))
        form_frame.columnconfigure(1, weight=1)
        self._frames.append(form_frame)

        lbl_cmd = tk.Label(form_frame, text="Befehl zur Erkennung:", font=("Segoe UI", 9))
        lbl_cmd.grid(row=0, column=0, sticky="w", pady=4, padx=(0, 12))
        self._labels.append(lbl_cmd)

        self.entry_cmd = tk.Entry(
            form_frame,
            font=("Segoe UI", 9),
            relief="flat",
            highlightthickness=1,
        )
        self.entry_cmd.grid(row=0, column=1, sticky="ew", pady=4, ipady=4)
        self._entries.append(self.entry_cmd)

        lbl_name = tk.Label(form_frame, text="Name (optional):", font=("Segoe UI", 9))
        lbl_name.grid(row=1, column=0, sticky="w", pady=4, padx=(0, 12))
        self._labels.append(lbl_name)

        self.entry_name = tk.Entry(
            form_frame,
            font=("Segoe UI", 9),
            relief="flat",
            highlightthickness=1,
        )
        self.entry_name.grid(row=1, column=1, sticky="ew", pady=4, ipady=4)
        self._entries.append(self.entry_name)

        lbl_path = tk.Label(form_frame, text="Pfad zur Anwendung (.exe):", font=("Segoe UI", 9))
        lbl_path.grid(row=2, column=0, sticky="w", pady=4, padx=(0, 12))
        self._labels.append(lbl_path)

        path_row = tk.Frame(form_frame)
        path_row.grid(row=2, column=1, sticky="ew", pady=4)
        self._frames.append(path_row)

        self.entry_path = tk.Entry(
            path_row,
            font=("Segoe UI", 9),
            relief="flat",
            highlightthickness=1,
        )
        self.entry_path.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))
        self._entries.append(self.entry_path)

        self.btn_browse = tk.Button(
            path_row,
            text="Durchsuchen...",
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.browse_executable,
        )
        self.btn_browse.pack(side="right")
        self._secondary_buttons.append(self.btn_browse)

        action_row = tk.Frame(form_frame)
        action_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self._frames.append(action_row)

        self.btn_add = tk.Button(
            action_row,
            text="Hinzufügen",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=18,
            pady=5,
            cursor="hand2",
            command=self.add_command,
        )
        self.btn_add.pack(side="left", padx=(0, 12))
        self._primary_buttons.append(self.btn_add)

        self.lbl_cmd_status = tk.Label(action_row, text="", font=("Segoe UI", 9))
        self.lbl_cmd_status.pack(side="left", fill="x", expand=True)

        list_header = tk.Label(
            content_frame,
            text="Gespeicherte Befehle",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        list_header.pack(fill="x", pady=(0, 6))
        self._headers.append(list_header)

        list_container = tk.Frame(content_frame)
        list_container.pack(fill="both", expand=True)
        self._frames.append(list_container)

        self.tree = ttk.Treeview(
            list_container,
            columns=("befehl", "name", "pfad"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("befehl", text="Befehl")
        self.tree.heading("name", text="Name")
        self.tree.heading("pfad", text="Programmpfad")

        self.tree.column("befehl", width=140, minwidth=100, anchor="w")
        self.tree.column("name", width=140, minwidth=100, anchor="w")
        self.tree.column("pfad", width=340, minwidth=160, anchor="w")

        self.tree_scroll = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=self.tree_scroll.set)

        self.tree_scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        footer_row = tk.Frame(content_frame)
        footer_row.pack(fill="x", pady=(8, 0))
        self._frames.append(footer_row)

        self.btn_delete = tk.Button(
            footer_row,
            text="Ausgewählten Befehl löschen",
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.delete_selected_command,
        )
        self.btn_delete.pack(side="left", padx=(0, 12))
        self._secondary_buttons.append(self.btn_delete)

        self.lbl_list_status = tk.Label(footer_row, text="", font=("Segoe UI", 9))
        self.lbl_list_status.pack(side="left", fill="x", expand=True)

    def apply_theme(self, theme_name: str) -> None:
        colors = THEMES.get(theme_name, THEMES["Dunkel"])
        self.current_theme = theme_name
        self.current_colors = colors

        self.root.configure(bg=colors["bg"])

        self.style.configure(
            "TNotebook",
            background=colors["bg"],
            borderwidth=0,
            tabmargins=[0, 0, 0, 0],
        )
        self.style.configure(
            "TNotebook.Tab",
            background=colors["input_bg"],
            foreground=colors["fg"],
            padding=[16, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        self.style.map(
            "TNotebook.Tab",
            background=[
                ("selected", colors["button_bg"]),
                ("active", colors["button_bg"]),
            ],
            foreground=[
                ("selected", colors["accent"]),
                ("active", colors["accent"]),
            ],
        )

        self.style.configure(
            "Treeview",
            background=colors["input_bg"],
            foreground=colors["fg"],
            fieldbackground=colors["input_bg"],
            borderwidth=0,
            font=("Segoe UI", 9),
            rowheight=26,
        )
        self.style.configure(
            "Treeview.Heading",
            background=colors["button_bg"],
            foreground=colors["button_fg"],
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", colors["accent"])],
            foreground=[("active", colors["accent_fg"])],
        )
        self.style.map(
            "Treeview",
            background=[("selected", colors["accent"])],
            foreground=[("selected", colors["accent_fg"])],
        )

        self.style.configure(
            "TCombobox",
            fieldbackground=colors["input_bg"],
            background=colors["button_bg"],
            foreground=colors["input_fg"],
            arrowcolor=colors["fg"],
            borderwidth=0,
            padding=4,
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["input_bg"])],
            foreground=[("readonly", colors["input_fg"])],
            background=[("readonly", colors["button_bg"])],
        )

        self.style.configure(
            "Vertical.TScrollbar",
            background=colors["button_bg"],
            troughcolor=colors["bg"],
            bordercolor=colors["bg"],
            arrowcolor=colors["fg"],
            borderwidth=0,
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[("active", colors["accent"]), ("pressed", colors["accent"])],
        )

        self.root.option_add("*TCombobox*Listbox.background", colors["input_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", colors["input_fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", colors["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", colors["accent_fg"])

        for frame in self._frames:
            frame.configure(bg=colors["bg"])

        for label in self._labels:
            label.configure(bg=colors["bg"], fg=colors["fg"])

        for header in self._headers:
            header.configure(bg=colors["bg"], fg=colors["accent"])

        for muted in self._muted_labels:
            muted.configure(bg=colors["bg"], fg=colors["muted"])

        for entry in self._entries:
            entry.configure(
                bg=colors["input_bg"],
                fg=colors["input_fg"],
                insertbackground=colors["accent"],
                highlightbackground=colors["border"],
                highlightcolor=colors["accent"],
            )

        if self.placeholder_active:
            self.entry_input.configure(fg=colors["muted"])
        else:
            self.entry_input.configure(fg=colors["input_fg"])

        for btn in self._primary_buttons:
            btn.configure(
                bg=colors["accent"],
                fg=colors["accent_fg"],
                activebackground=colors["button_bg"],
                activeforeground=colors["button_fg"],
            )

        for btn in self._secondary_buttons:
            btn.configure(
                bg=colors["button_bg"],
                fg=colors["button_fg"],
                activebackground=colors["accent"],
                activeforeground=colors["accent_fg"],
            )

        if self.voice_recognizer and getattr(self.voice_recognizer, "is_listening", False):
            self.btn_voice.configure(
                bg=colors["accent"],
                fg=colors["accent_fg"],
            )

        self.chat_text.configure(
            bg=colors["input_bg"],
            fg=colors["fg"],
            insertbackground=colors["accent"],
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"],
        )

        self.chat_text.tag_configure("user", foreground=colors["user"], font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_configure("user_text", foreground=colors["fg"], font=("Segoe UI", 10))
        self.chat_text.tag_configure("bot", foreground=colors["bot"], font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_configure("bot_text", foreground=colors["fg"], font=("Segoe UI", 10))
        self.chat_text.tag_configure("bot_error", foreground=colors["error"], font=("Segoe UI", 10))
        self.chat_text.tag_configure("system", foreground=colors["muted"], font=("Segoe UI", 9, "italic"))
        self.chat_text.tag_configure("time", foreground=colors["muted"], font=("Segoe UI", 8))

        self.lbl_cmd_status.configure(bg=colors["bg"])
        self.lbl_list_status.configure(bg=colors["bg"])
        self.lbl_voice_status.configure(bg=colors["bg"])

    def _on_theme_changed(self, event=None) -> None:
        selected_theme = self.combo_theme.get()
        if self.config_manager and hasattr(self.config_manager, "set_theme"):
            self.config_manager.set_theme(selected_theme)
        self.apply_theme(selected_theme)

    def _on_entry_focus_in(self, event=None) -> None:
        if self.placeholder_active:
            self.entry_input.delete(0, tk.END)
            self.entry_input.configure(fg=self.current_colors.get("input_fg", "#cdd6f4"))
            self.placeholder_active = False

    def _on_entry_focus_out(self, event=None) -> None:
        if not self.entry_input.get().strip():
            self.placeholder_active = True
            self.entry_input.delete(0, tk.END)
            self.entry_input.insert(0, self.placeholder_text)
            self.entry_input.configure(fg=self.current_colors.get("muted", "#9399b2"))

    def send_command(
        self,
        event=None,
        command_override: Optional[str] = None,
        sender: str = "Du",
    ) -> None:
        if command_override is not None:
            command_text = command_override.strip()
        else:
            if self.placeholder_active:
                return
            command_text = self.entry_input.get().strip()
            if not command_text:
                return
            self.entry_input.delete(0, tk.END)

        if not command_text:
            return

        self._append_message(sender, command_text, tag="user")

        if not self.assistant:
            self._append_message("Assistent", "Kein Assistenten-Backend verknüpft.", tag="bot_error")
            return

        response = self.assistant.process_command(command_text)
        erfolg = getattr(response, "erfolg", False)
        antwort_text = getattr(response, "antwort_text", str(response))
        aktion = getattr(response, "aktion", None)

        bot_tag = "bot" if erfolg else "bot_error"
        self._append_message("Assistent", antwort_text, tag=bot_tag)

        if aktion == "exit":
            self.entry_input.configure(state="disabled")
            self.btn_send.configure(state="disabled")
            self.btn_voice.configure(state="disabled")
            self.root.after(800, self._exit_cleanly)

    def start_voice_input(self) -> None:
        if not self.voice_recognizer:
            self._set_status(self.lbl_voice_status, "Spracherkennung nicht verfügbar.", is_error=True)
            return
        if getattr(self.voice_recognizer, "is_listening", False):
            return
        self._set_voice_ui_listening()
        self.voice_recognizer.listen_once(
            on_success=self._on_voice_success,
            on_status=self._on_voice_status,
            on_error=self._on_voice_error,
        )

    def _set_voice_ui_listening(self) -> None:
        accent_color = self.current_colors.get("accent", "#89b4fa")
        accent_fg = self.current_colors.get("accent_fg", "#11111b")
        self.btn_voice.configure(
            text="🔴 Höre zu...",
            bg=accent_color,
            fg=accent_fg,
        )
        self.lbl_voice_status.configure(
            text="Höre zu...",
            fg=accent_color,
        )

    def _reset_voice_button(self) -> None:
        btn_bg = self.current_colors.get("button_bg", "#45475a")
        btn_fg = self.current_colors.get("button_fg", "#ffffff")
        self.btn_voice.configure(
            text="🎤 Sprechen",
            bg=btn_bg,
            fg=btn_fg,
        )

    def _on_voice_status(self, status_msg: str) -> None:
        self.root.after(0, lambda: self._apply_voice_status(status_msg))

    def _apply_voice_status(self, status_msg: str) -> None:
        accent_color = self.current_colors.get("accent", "#89b4fa")
        accent_fg = self.current_colors.get("accent_fg", "#11111b")
        btn_bg = self.current_colors.get("button_bg", "#45475a")
        btn_fg = self.current_colors.get("button_fg", "#ffffff")

        if status_msg == "Verarbeite Audio...":
            self.btn_voice.configure(
                text="⏳ Verarbeite...",
                bg=btn_bg,
                fg=btn_fg,
            )
        elif status_msg == "Höre zu...":
            self.btn_voice.configure(
                text="🔴 Höre zu...",
                bg=accent_color,
                fg=accent_fg,
            )
        self.lbl_voice_status.configure(text=status_msg, fg=accent_color)

    def _on_voice_success(self, recognized_text: str) -> None:
        self.root.after(0, lambda: self._apply_voice_success(recognized_text))

    def _apply_voice_success(self, recognized_text: str) -> None:
        self._reset_voice_button()
        self.lbl_voice_status.configure(text="")
        self.send_command(command_override=recognized_text, sender="Du (Sprache)")

    def _on_voice_error(self, error_msg: str) -> None:
        self.root.after(0, lambda: self._apply_voice_error(error_msg))

    def _apply_voice_error(self, error_msg: str) -> None:
        self._reset_voice_button()
        self._set_status(self.lbl_voice_status, error_msg, is_error=True)

    def _append_message(self, sender: str, text: str, tag: str = "bot") -> None:
        self.chat_text.configure(state="normal")
        timestamp = datetime.datetime.now().strftime("%H:%M")
        self.chat_text.insert(tk.END, f"[{timestamp}] ", "time")
        self.chat_text.insert(tk.END, f"{sender}: ", tag)

        text_tag = f"{tag}_text" if tag in ("user", "bot") else tag
        self.chat_text.insert(tk.END, f"{text}\n\n", text_tag)

        self.chat_text.configure(state="disabled")
        self.chat_text.see(tk.END)

    def _show_welcome(self) -> None:
        self.chat_text.configure(state="normal")
        self.chat_text.insert(
            tk.END,
            "Desktop Assistent bereit.\n"
            "Tippe 'hilfe' für eine Liste der verfügbaren Befehle.\n\n",
            "system",
        )
        self.chat_text.configure(state="disabled")
        self.chat_text.see(tk.END)

    def browse_executable(self) -> None:
        selected_file = filedialog.askopenfilename(
            title="Anwendung auswählen",
            filetypes=[
                ("Ausführbare Dateien (*.exe)", "*.exe"),
                ("Alle Dateien (*.*)", "*.*"),
            ],
        )
        if selected_file:
            clean_path = selected_file.replace("/", "\\")
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, clean_path)

            base_name = os.path.splitext(os.path.basename(clean_path))[0]
            if not self.entry_name.get().strip():
                self.entry_name.insert(0, base_name.capitalize())
            if not self.entry_cmd.get().strip():
                self.entry_cmd.insert(0, base_name.lower())

    def add_command(self) -> None:
        befehl = self.entry_cmd.get().strip()
        name = self.entry_name.get().strip()
        pfad = self.entry_path.get().strip()

        if not befehl or not pfad:
            self._set_status(
                self.lbl_cmd_status,
                "Bitte Befehl und Anwendungspfad angeben.",
                is_error=True,
            )
            return

        erfolg = False
        if self.config_manager:
            if hasattr(self.config_manager, "add_programme"):
                erfolg = self.config_manager.add_programme(befehl, pfad, name)
            elif hasattr(self.config_manager, "add_custom_command"):
                erfolg = self.config_manager.add_custom_command(befehl, pfad, name)

        if erfolg:
            self.refresh_command_list()
            self.entry_cmd.delete(0, tk.END)
            self.entry_name.delete(0, tk.END)
            self.entry_path.delete(0, tk.END)
            self._set_status(
                self.lbl_cmd_status,
                f"Befehl '{befehl}' erfolgreich hinzugefügt.",
                is_error=False,
            )
        else:
            self._set_status(
                self.lbl_cmd_status,
                "Fehler beim Speichern des Befehls.",
                is_error=True,
            )

    def delete_selected_command(self) -> None:
        selected = self.tree.selection()
        if not selected:
            self._set_status(
                self.lbl_list_status,
                "Bitte wählen Sie einen Befehl aus der Liste aus.",
                is_error=True,
            )
            return

        item = self.tree.item(selected[0])
        values = item.get("values", [])
        if not values:
            return

        befehl = str(values[0])
        erfolg = False
        if self.config_manager:
            if hasattr(self.config_manager, "remove_programme"):
                erfolg = self.config_manager.remove_programme(befehl)
            elif hasattr(self.config_manager, "remove_custom_command"):
                erfolg = self.config_manager.remove_custom_command(befehl)

        if erfolg:
            self.refresh_command_list()
            self._set_status(
                self.lbl_list_status,
                f"Befehl '{befehl}' wurde erfolgreich gelöscht.",
                is_error=False,
            )
        else:
            self._set_status(
                self.lbl_list_status,
                f"Befehl '{befehl}' konnte nicht gelöscht werden.",
                is_error=True,
            )

    def refresh_command_list(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.config_manager:
            return

        commands: List[Dict[str, str]] = []
        if hasattr(self.config_manager, "get_programme"):
            commands = self.config_manager.get_programme()
        elif hasattr(self.config_manager, "get_custom_commands"):
            commands = self.config_manager.get_custom_commands()

        for cmd in commands:
            self.tree.insert(
                "",
                "end",
                values=(
                    cmd.get("befehl", ""),
                    cmd.get("name", ""),
                    cmd.get("pfad", ""),
                ),
            )

    def _on_tree_double_click(self, event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item.get("values", [])
        if len(values) >= 3:
            self.entry_cmd.delete(0, tk.END)
            self.entry_cmd.insert(0, str(values[0]))
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, str(values[1]))
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, str(values[2]))

    def _set_status(self, label: tk.Label, text: str, is_error: bool = False) -> None:
        color = self.current_colors.get("error", "#f38ba8") if is_error else self.current_colors.get("bot", "#a6e3a1")
        label.configure(text=text, fg=color)
        self.root.after(4000, lambda: label.configure(text=""))

    def _exit_cleanly(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self) -> None:
        self.root.mainloop()
