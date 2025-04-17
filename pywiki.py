import os
import sys
import configparser
import wikipedia 
import webbrowser
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton, 
                            QLineEdit, QComboBox, QLabel, QTabWidget, QListWidget, 
                            QHBoxLayout, QScrollArea, QFontDialog, QColorDialog, QAction,
                            QMenu)

languages = {'EN': 'en', 'RU': 'ru', 'DE': 'de', 'FR': 'fr', 'ES': 'es', 
            'ZH': 'zh', 'JA': 'ja', 'KO': 'ko'}

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(30)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.title_label = QLabel("Wikipedia Search (made by Vafls, forked from Xeon)")
        self.title_label.setStyleSheet("color: #eceff4; padding-left: 10px;")
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(0)
        
        self.min_button = QPushButton("-")
        self.min_button.setFixedSize(30, 30)
        self.min_button.clicked.connect(self.parent.showMinimized)
        
        self.max_button = QPushButton("□")
        self.max_button.setFixedSize(30, 30)
        self.max_button.clicked.connect(self.toggle_maximize)
        
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.parent.close)
        
        for btn in [self.min_button, self.max_button, self.close_button]:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; 
                    color: #eceff4;
                    border: none;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 30);
                }
            """)
        
        controls_layout.addWidget(self.min_button)
        controls_layout.addWidget(self.max_button)
        controls_layout.addWidget(self.close_button)
        
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addLayout(controls_layout)

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

class WikipediaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.lang = 'EN'
        wikipedia.set_lang(languages[self.lang])
        self.setGeometry(100, 100, 1024, 768)
        
        # Настройки по умолчанию
        self.current_font = QtGui.QFont('Segoe Script', 12)
        self.bg_color = "#2e3440"
        self.title_bar_color = "#2e3440"
        
        self.setWindowIcon(QtGui.QIcon('wiki.ico'))
        self.history = []
        self.drag_pos = QPoint()
        
        # Инициализация UI
        self.initUI()
        
        # Загрузка настроек после инициализации UI
        self.load_settings()

    def initUI(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #4c566a; }
            QTabBar::tab { 
                background: #3b4252; 
                color: #eceff4; 
                padding: 10px; 
                border: 1px solid #4c566a; 
                border-radius: 5px;
            }
            QTabBar::tab:selected { background: #81a1c1; color: #2e3440; }
            QTabBar::tab:hover { background: #5e81ac; }
        """)
        main_layout.addWidget(self.tabs)

        # Вкладка поиска
        self.search_tab = QWidget()
        self.tabs.addTab(self.search_tab, "Search")
        self.init_search_tab()

        # Вкладка истории
        self.history_tab = QWidget()
        self.tabs.addTab(self.history_tab, "History")
        self.init_history_tab()

        # Вкладка настроек
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Settings")
        self.init_settings_tab()

        self.setCentralWidget(central_widget)
        self.init_context_menu()
        
        # Применение стилей
        self.update_colors()

    def init_context_menu(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        font_action = menu.addAction("Change Font")
        font_action.triggered.connect(self.change_font)
        color_action = menu.addAction("Change Background")
        color_action.triggered.connect(self.change_background_color)
        menu.exec_(self.mapToGlobal(pos))

    def init_search_tab(self):
        layout = QVBoxLayout(self.search_tab)

        self.label = QLabel("Enter your query:\n(All results are saved as text files and listed in history)")
        self.label.setFont(QtGui.QFont('Ink Free', 16))
        self.label.setStyleSheet("color:#d8dee9;")
        layout.addWidget(self.label)

        input_layout = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Enter search query here")
        self.entry.setFont(self.current_font)
        self.entry.setStyleSheet("""
            background-color:#3b4252;
            color:#eceff4;
            border:1px solid #4c566a;
            padding:5px;
        """)
        self.entry.returnPressed.connect(self.search_wikipedia)
        input_layout.addWidget(self.entry)

        self.language_menu = QComboBox()
        self.language_menu.addItems(languages.keys())
        self.language_menu.setCurrentText(self.lang)
        self.language_menu.currentTextChanged.connect(self.switch_language)
        self.language_menu.setStyleSheet("""
            QComboBox {
                background-color:#3b4252;
                color:#eceff4;
                border:1px solid #4c566a;
                padding:5px;
            }
            QComboBox QAbstractItemView {
                background-color:#4c566a;
                color:#eceff4;
            }
        """)
        input_layout.addWidget(self.language_menu)

        self.search_button = QPushButton("🔎 Search")
        self.search_button.clicked.connect(self.search_wikipedia)
        self.search_button.setStyleSheet("""
            background-color:#81a1c1;
            color:#2e3440;
            padding:5px;
            border-radius:5px;
        """)
        input_layout.addWidget(self.search_button)
        layout.addLayout(input_layout)

        self.text_area = QTextEdit()
        self.text_area.setFont(self.current_font)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            background-color:#3b4252;
            color:#eceff4;
            border:1px solid #4c566a;
            padding:10px;
        """)
        layout.addWidget(self.text_area)

        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("background-color:#3b4252; border:none;")
        self.scroll_area.setWidgetResizable(True)
        self.button_container = QWidget()
        self.button_layout = QVBoxLayout(self.button_container)
        self.scroll_area.setWidget(self.button_container)
        layout.addWidget(self.scroll_area)
        self.scroll_area.setVisible(False)

    def init_history_tab(self):
        layout = QVBoxLayout(self.history_tab)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color:#3b4252;
                color:#eceff4;
                border:1px solid #4c566a;
            }
            QListWidget::item {
                padding:10px;
                border:1px solid #4c566a;
                margin:2px;
            }
            QListWidget::item:selected {
                background-color:#81a1c1;
                color:#2e3440;
            }
        """)
        self.history_list.itemClicked.connect(self.handle_history_click)
        layout.addWidget(self.history_list)

        self.history_text_area = QTextEdit()
        self.history_text_area.setFont(self.current_font)
        self.history_text_area.setReadOnly(True)
        self.history_text_area.setStyleSheet("""
            background-color:#3b4252;
            color:#eceff4;
            border:1px solid #4c566a;
            padding:10px;
        """)
        layout.addWidget(self.history_text_area)

    def init_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.setAlignment(Qt.AlignTop)

        font_group = QWidget()
        font_layout = QVBoxLayout(font_group)
        font_label = QLabel("Font Settings:")
        font_label.setFont(QtGui.QFont('Arial', 12, QtGui.QFont.Bold))
        font_layout.addWidget(font_label)
        
        self.font_button = QPushButton("Change Application Font")
        self.font_button.clicked.connect(self.change_font)
        self.font_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background: #81a1c1;
                color: #2e3440;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #5e81ac;
            }
        """)
        font_layout.addWidget(self.font_button)
        layout.addWidget(font_group)

        color_group = QWidget()
        color_layout = QVBoxLayout(color_group)
        color_label = QLabel("Color Settings:")
        color_label.setFont(QtGui.QFont('Arial', 12, QtGui.QFont.Bold))
        color_layout.addWidget(color_label)
        
        self.color_button = QPushButton("Change Background Color")
        self.color_button.clicked.connect(self.change_background_color)
        self.color_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background: #81a1c1;
                color: #2e3440;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #5e81ac;
            }
        """)
        color_layout.addWidget(self.color_button)
        layout.addWidget(color_group)

        layout.addStretch()

    def change_font(self):
        font, ok = QFontDialog.getFont(self.current_font, self)
        if ok:
            self.current_font = font
            self.apply_font(font)
            self.save_settings()

    def apply_font(self, font):
        widgets = [
            self.text_area, 
            self.history_text_area,
            self.label,
            self.entry,
            self.history_list,
            self.font_button,
            self.color_button
        ]
        for widget in widgets:
            widget.setFont(font)

    def change_background_color(self):
        color = QColorDialog.getColor(QtGui.QColor(self.bg_color))
        if color.isValid():
            self.bg_color = color.name()
            self.title_bar_color = self.bg_color
            self.update_colors()
            self.save_settings()

    def update_colors(self):
        darker_bg = self.darker_color(self.bg_color)
        self.setStyleSheet(f"""
            WikipediaApp {{ background-color: {self.bg_color}; }}
            QTextEdit, QListWidget, QLineEdit, QComboBox, QTabWidget::pane {{
                background-color: {darker_bg};
                color: #eceff4;
            }}
            QTabBar::tab {{
                background: {darker_bg};
                border: 1px solid {self.darker_color(self.bg_color, 0.8)};
            }}
        """)
        self.title_bar.setStyleSheet(f"background-color: {self.bg_color};")

    def darker_color(self, hex_color, factor=0.7):
        color = QtGui.QColor(hex_color)
        return f"rgb({int(color.red()*factor)}, {int(color.green()*factor)}, {int(color.blue()*factor)})"

    def save_settings(self):
        config = configparser.ConfigParser()
        config['SETTINGS'] = {
            'font_family': self.current_font.family(),
            'font_size': str(self.current_font.pointSize()),
            'font_bold': str(self.current_font.bold()),
            'font_italic': str(self.current_font.italic()),
            'bg_color': self.bg_color
        }
        
        with open('settings.cfg', 'w') as configfile:
            config.write(configfile)

    def load_settings(self):
        if not os.path.exists('settings.cfg'):
            return

        config = configparser.ConfigParser()
        config.read('settings.cfg')
        
        try:
            if 'SETTINGS' in config:
                settings = config['SETTINGS']
                
                font = QtGui.QFont()
                font.setFamily(settings.get('font_family', 'Segoe Script'))
                font.setPointSize(int(settings.get('font_size', 12)))
                font.setBold(settings.getboolean('font_bold', False))
                font.setItalic(settings.getboolean('font_italic', False))
                self.current_font = font
                
                self.bg_color = settings.get('bg_color', '#2e3440')
                self.title_bar_color = self.bg_color
                
                self.apply_font(font)
                self.update_colors()
        except Exception as e:
            print(f"Error loading settings: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            delta = event.globalPos() - self.drag_pos
            self.move(self.pos() + delta)
            self.drag_pos = event.globalPos()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def switch_language(self, new_lang):
        self.lang = new_lang
        wikipedia.set_lang(languages[self.lang])

    def search_wikipedia(self):
        query = self.entry.text().strip()
        if not query:
            self.text_area.setPlainText("Please enter a query.")
            return

        try:
            result = wikipedia.page(query)
            content = result.content
            filename = f"{query}_{languages[self.lang]}.txt"
            with open(filename, "w", encoding="utf-8") as file:
                file.write(content)
            self.text_area.setPlainText(content)
            self.scroll_area.setVisible(False)

            if (query, self.lang) not in self.history:
                self.history.append((query, self.lang))
                self.history_list.addItem(f"{query} ({self.lang})")
            self.save_history()

        except wikipedia.exceptions.DisambiguationError as e:
            options = e.options
            self.text_area.clear()
            self.text_area.setPlainText("Disambiguation options found. Select one:")

            for i in reversed(range(self.button_layout.count())):
                self.button_layout.itemAt(i).widget().setParent(None)

            for option in options:
                button = QPushButton(option)
                button.setStyleSheet("""
                    background-color:#5e81ac;
                    color:#eceff4;
                    border-radius:5px;
                    padding:5px;
                """)
                button.clicked.connect(lambda _, opt=option: self.open_in_browser(opt))
                self.button_layout.addWidget(button)

            self.scroll_area.setVisible(True)

        except wikipedia.exceptions.PageError:
            self.text_area.setPlainText("Nothing was found on Wikipedia.")
            self.scroll_area.setVisible(False)

    def open_in_browser(self, option):
        try:
            search_url = f"https://{languages[self.lang]}.wikipedia.org/wiki/{option.replace(' ', '_')}"
            webbrowser.open(search_url)
        except wikipedia.exceptions.DisambiguationError as e:
            search_url = f"https://{languages[self.lang]}.wikipedia.org/wiki/Special:Search?search={option.replace(' ', '+')}"
            webbrowser.open(search_url)
        except wikipedia.exceptions.PageError:
            self.text_area.setPlainText("Error: Article not found.")

    def handle_history_click(self, item):
        text = item.text()
        query, lang = text.rsplit(" ", 1)
        query = query.strip()
        lang = lang.strip("()")
        self.switch_language(lang)
        filename = f"{query}_{languages[lang]}.txt"
        if os.path.isfile(filename):
            with open(filename, "r", encoding="utf-8") as file:
                content = file.read()
            self.history_text_area.setPlainText(content)
        else:
            self.history_text_area.setPlainText("File not found.")

    def save_history(self):
        with open("previous_search.txt", "w", encoding="utf-8") as file:
            for query, lang in self.history:
                file.write(f"{query} ({lang})\n")

    def load_history(self):
        if os.path.isfile("previous_search.txt"):
            with open("previous_search.txt", "r", encoding="utf-8") as file:
                lines = file.readlines()
                for line in lines:
                    if " (" in line and line.endswith(")\n"):
                        query, lang = line.rsplit(" ", 1)
                        query = query.strip()
                        lang = lang.strip("()\n")
                        self.history.append((query, lang))
                        self.history_list.addItem(f"{query} ({lang})")

    def closeEvent(self, event):
        self.save_history()
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('wiki.ico'))
    main_window = WikipediaApp()
    main_window.load_history()
    main_window.show()
    sys.exit(app.exec_())