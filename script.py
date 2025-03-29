import cv2
import easyocr
import numpy as np
import sys
import json
import os
from PyQt6.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QHBoxLayout, QComboBox, QLineEdit, QMessageBox, QListWidget, QListWidgetItem
from PyQt6.QtGui import QPixmap, QImage, QPalette, QColor
from PyQt6.QtCore import QTimer, Qt


class OCRApp(QWidget):
    def __init__(self):
        super().__init__()

        # 🔵 EasyOCR Reader einmalig initialisieren
        self.reader = easyocr.Reader(["en"])
        #self.readerjpn = easyocr.Reader(["ja"])

        # Initialize hide_timer
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.hide_scoreboard)

        # Initialize team_tags
        self.team_tags = {}
     
        # Initialize team_containers
        self.team_containers = {}  # Add this line to define team_containers
      
        # Initialize OCR running state
        self.is_ocr_running = False  
        self.is_paused = False

        # 🌟 Hauptlayout
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Tabs erstellen
        self.tabs.addTab(self.create_control_tab(), "Main Control")
        self.tabs.addTab(self.create_settings_tab(), "Score-Settings")
        self.tabs.addTab(self.create_video_tab(), "Video-Setup")
        self.tabs.addTab(self.create_log_tab(), "OCR-Process")
        #self.tabs.addTab(self.create_table_tab(), "Table")
        self.tabs.addTab(self.create_table_settings_tab(), "Table-Settings")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.selected_team_size = None  # Speichert die Teamgröße
        self.team_tag_inputs = []  # Speichert die Eingabefelder

        # 🌟 Fenster-Styling
        self.setStyleSheet("""
            background-color: #222;
            color: white;
        """)

        self.setWindowTitle("mk8dx Scoreboard")
        self.resize(800, 600)

        self.capture = None  # Speichert die aktive Capture Card
        self.timer = QTimer(self)  # Timer für Live-Feed-Update
        self.timer.timeout.connect(self.update_frame)  # Timer mit Update-Funktion verbinden

        # Scoreboard Cleanfeed-Fenster erstellen
        self.scoreboard_window = ScoreboardWindow()
        self.scoreboard_window.set_table_widget(self.create_table_tab())  # Score-Tabelle ins Fenster packen

        # Fenster anzeigen
        self.scoreboard_window.show()

        # Tabelle beim Start aktualisieren
        self.update_score_table()
        self.update_score_list()




    # 🔹 Tab 1: Steuerung & Einstellungen
    def create_control_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()


         # Modusauswahl
        mode_layout = QHBoxLayout()
        self.mode2_btn = QPushButton("2v2")
        self.mode3_btn = QPushButton("3v3")
        self.mode4_btn = QPushButton("4v4")
        self.mode6_btn = QPushButton("6v6")
        

        # Button-Größe anpassen
        for btn in [self.mode2_btn, self.mode3_btn, self.mode4_btn, self.mode6_btn]:
            btn.setFixedSize(70, 40)  # Breite 120px, Höhe 40px
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3671c9;
                    color: white; 
                    font-size: 14px; 
                    border-radius: 5px;
                }
                QPushButton:pressed {
                    background-color: #1372ae;
                }
                              """)
            mode_layout.addWidget(btn)

        mode_layout.addWidget(self.mode2_btn)
        mode_layout.addWidget(self.mode3_btn)
        mode_layout.addWidget(self.mode4_btn)
        mode_layout.addWidget(self.mode6_btn)

        self.mode2_btn.clicked.connect(lambda: self.set_team_size(2))
        self.mode3_btn.clicked.connect(lambda: self.set_team_size(3))
        self.mode4_btn.clicked.connect(lambda: self.set_team_size(4))
        self.mode6_btn.clicked.connect(lambda: self.set_team_size(5))


        layout.addLayout(mode_layout)

        # 📌 Container für Eingabefelder
        self.team_tag_container = QVBoxLayout()
        layout.addLayout(self.team_tag_container)

        # 🏆 "Tags speichern"-Button und Info-Button in einer Zeile
        apply_btn_layout = QHBoxLayout()

        # 🏆 "Apply Team-Tags"-Button
        self.apply_tags_btn = QPushButton("Apply Team-Tags")
        self.apply_tags_btn.clicked.connect(self.apply_team_tags)
        self.apply_tags_btn.setFixedSize(200, 40)
        self.apply_tags_btn.setStyleSheet("""
            QPushButton {
                background-color: orange; 
                color: black; 
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: darkorange;
            }
        """)
        apply_btn_layout.addWidget(self.apply_tags_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 🏆 "Info"-Button
        applytags_info_button = QPushButton("i")
        applytags_info_button.clicked.connect(lambda: self.show_info("""
        Team1 will be shown in golden color.
        Applying tags will update the Scoreboard.
        For 6v6, run the manual trigger without tags and use the result from the process-tab.
                                                                     
        Team1 wird in goldener Farbe angezeigt.
        Tags anwenden aktualisiert das Scoreboard.
        Für 6v6, benutze den manuellen Trigger ohne Tags und trage das Ergebnis aus dem Prozess-Tab als Tag ein.                                                                                                                                                                               
        """))
        applytags_info_button.setFixedSize(20, 20)  
        applytags_info_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                font-size: 18px;
                border-radius: 10px;  /* Runde Form */
            }
            QPushButton:pressed {
                background-color: blue;
            }
        """)
        apply_btn_layout.addWidget(applytags_info_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Füge die Zeile mit den Buttons ins Hauptlayout ein
        layout.addLayout(apply_btn_layout)



        # Start-Button Styling & Standardmäßig deaktiviert
        start_btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedSize(150, 50)
        self.start_btn.setEnabled(False)  # Button erst deaktivieren!
        self.condition1 = False
        self.condition2 = False
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: green;
                color: white;
                font-size: 16px;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:pressed {
                background-color: darkgreen;
            }
            QPushButton:disabled {
                background-color: gray;
                color: darkgray;
            }
        """)

        self.start_btn.clicked.connect(self.toggle_ocr)
        start_btn_layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)


            # 🏆 "Info"-Button
        start_info_button = QPushButton("i")
        start_info_button.setFixedSize(20, 20)  
        start_info_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                font-size: 18px;
                border-radius: 10px;  /* Runde Form */
            }
            QPushButton:pressed {
                background-color: blue;
            }
        """)
        start_info_button.clicked.connect(lambda: self.show_info("""
        The program triggers with the 12th player shown.
        After a successful run, the program is set on 120s cooldown, so you can freely browse your Library.
                                                                 

        Das Programm löst aus, wenn der 12. Spieler angezeigt wird.
        Nach einem Lauf hat das Programm 120s Cooldown, damit du ohne Probleme in deine Galerie gucken kannst.                                                                                                                                                                                                                                 
"""))
        start_btn_layout.addWidget(start_info_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Füge die Zeile mit den Buttons ins Hauptlayout ein
        layout.addLayout(start_btn_layout)


        # Reset Button Einstellungen
        reset_btn_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_scores)
        self.reset_btn.clicked.connect(self.reset_race_count)
        self.reset_btn.setFixedSize(100, 30)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: red;
                color: white;
                font-size: 16px;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: darkred;
            }
        """)
        reset_btn_layout.addWidget(self.reset_btn, alignment=Qt.AlignmentFlag.AlignCenter)


                    # 🏆 "Info"-Button
        reset_info_button = QPushButton("i")
        reset_info_button.setFixedSize(20, 20)  
        reset_info_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                font-size: 18px;
                border-radius: 10px;  /* Runde Form */
            }
            QPushButton:pressed {
                background-color: blue;
            }
        """)
        reset_info_button.clicked.connect(lambda: self.show_info("""
        Most of the Data is stored even if the program is closed, so make sure to Reset.
        Reset will delete all Team-Tags, Scores, Racecount and will stop the Automatic Mode.

        Die meisten Daten sind auch nach schließen des Programms gespeichert.
        Reset löscht alle Team-Tags, Scores, Rennzähler und stoppt den Automatik-Modus.                                                                                                                                                                                                                                    
        """))
        reset_btn_layout.addWidget(reset_info_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Füge die Zeile mit den Buttons ins Hauptlayout ein
        layout.addLayout(reset_btn_layout)


        # 🟢 Manueller OCR-Button
        manualocr_btn_layout = QHBoxLayout()
        self.manual_ocr_btn = QPushButton("Manual Trigger")
        self.manual_ocr_btn.clicked.connect(self.capture_image_for_ocr)
        self.manual_ocr_btn.setFixedSize(150, 40)
        self.manual_ocr_btn.setStyleSheet("""
            QPushButton { 
                background-color: #007ACC;
                color: white;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #005A8C;
            }
            """)

        # Buttons ins Layout setzen
        manualocr_btn_layout.addWidget(self.manual_ocr_btn, alignment=Qt.AlignmentFlag.AlignCenter)


            # 🏆 "Info"-Button
        manualocr_info_button = QPushButton("i")
        manualocr_info_button.setFixedSize(20, 20)  
        manualocr_info_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                font-size: 18px;
                border-radius: 10px;  /* Runde Form */
            }
            QPushButton:pressed {
                background-color: blue;
            }
        """)
        manualocr_info_button.clicked.connect(lambda: self.show_info("""
        Mainly kept for testing, feel free to use this to explore how the program works.
        You can retrieve single races and after start the automatic, and also get results without tags. 

        Sei eingeladen, hiermit auszuprobieren, wie das Programm funktioniert.
        Du kannst einzelne Rennen einlesen und nachträglich die Automatik starten.
        Ergebnisse werden auch ohne Tags angezeigt.                                                                                                                                                                                                                                                                                                                
        """))
        manualocr_btn_layout.addWidget(manualocr_info_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Füge die Zeile mit den Buttons ins Hauptlayout ein
        layout.addLayout(manualocr_btn_layout)


        tab.setLayout(layout)
        return tab


    def set_team_size(self, size):
        """ Erzeugt Eingabefelder für Team-Tags basierend auf der Teamgröße. """
        self.selected_team_size = size
        self.team_tag_inputs = []  # Zurücksetzen

        # 🧹 Vorherige Felder löschen
        for i in reversed(range(self.team_tag_container.count())):
            widget = self.team_tag_container.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 🏆 Neue Eingabefelder erzeugen
        num_teams = 12 // size  # Berechnung der Teamanzahl
        for i in range(num_teams):
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Team {i + 1} Tag")
            input_field.setFixedSize(200, 30)
            self.team_tag_container.addWidget(input_field)
            self.team_tag_inputs.append(input_field)  # Speichern für später

        print(f"✅ Teamgröße {size} ausgewählt!")



    # 🔹 Tab 2: Scores als Liste und Einstellungen zum manuellen korrigieren
    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # 📊 Score-Liste
        scorelist_layout = QHBoxLayout()
        self.score_list_widget = QListWidget()
        self.score_list_widget.setFixedSize(400, 300)
        self.score_list_widget.setStyleSheet("""
            QListWidget {  
                background-color: #333;
                color: white;
                font-size: 24px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #555;
            }
        """)
        scorelist_layout.addWidget(self.score_list_widget)

            # 🏆 "Info"-Button
        scorelist_info_button = QPushButton("i")
        scorelist_info_button.setFixedSize(20, 20)  
        scorelist_info_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                font-size: 18px;
                border-radius: 10px;  /* Runde Form */
            }
            QPushButton:pressed {
                background-color: blue;
            }
        """)
        scorelist_info_button.clicked.connect(lambda: self.show_info("""
        Here you will see all the Information collected.
        "Missing" indicates players not being assigned to a team, make sure to look at the process-tab.
        "Points Issue" indicates the total points not matching the racecount.

        Hier siehst du alle gesammelten Informationen.
        "Missing" zeigt Punkte von Spielern, die keinem Team zugeordnet werden konnten, schau dafür direkt in den Prozess-Tab.
        "Points Issue" zeigt an, das die Gesamtzahl an Punkten nicht mit der Rennzahl übereinstimmt.                                                                                                                                                                                                                                                                                                              
        """))
        scorelist_layout.addWidget(scorelist_info_button, alignment=Qt.AlignmentFlag.AlignLeft)

        # Füge die Zeile mit den Buttons ins Hauptlayout ein
        layout.addLayout(scorelist_layout)


        tab.setLayout(layout)
        return tab



    # 🔹 Tab 3: Video-Setup
    def create_video_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        capture_layout = QHBoxLayout()

        self.capture_btn = QPushButton("Connect Capture Card")
        self.capture_btn.setFixedSize(200, 50)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: orange;
                color: black;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: darkorange;
            }
        """)
        self.capture_btn.clicked.connect(self.find_capture_cards)  # Klick ruft `find_capture_cards()` auf
        capture_layout.addWidget(self.capture_btn)


            # 🏆 "Info"-Button
        capture_info_button = QPushButton("i")
        capture_info_button.setFixedSize(20, 20)  
        capture_info_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                font-size: 18px;
                border-radius: 10px;  /* Runde Form */
            }
            QPushButton:pressed {
                background-color: blue;
            }
        """)
        capture_info_button.clicked.connect(lambda: self.show_info("""
        The program searches for 10 external Video Devices connected to your Computer and lists what it finds.
        You will see the active Device below, make sure to see your Game Capture.

        Das Programm sucht nach 10 externen Video-Geräten angeschlossen an deinen Computer und listet sie auf. 
        Das aktive Gerät wird unten angezeigt, stelle sicher, dass du deine Spielaufnahme siehst.                                                                                                                                                                                
        """))
        capture_layout.addWidget(capture_info_button, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(capture_layout)


        # 🎥 Dropdown für Capture-Device Auswahl
        self.device_select = QComboBox()
        self.device_select.currentIndexChanged.connect(self.select_capture_device)
        layout.addWidget(self.device_select)
        
        # Vorschau Fenster für Capture Card
        self.video_label = QLabel("📷 Video-Feed")
        self.video_label.setFixedSize(640, 360)  # Oder eine andere passende Größe
        layout.addWidget(self.video_label)


        tab.setLayout(layout)
        return tab
    

    def find_capture_cards(self):
        self.condition2 = True
        self.check_conditions()
        self.device_select.clear()
        found_devices = []

        print("🔍 Suche nach Capture Cards...")

        # Testet die ersten 10 Geräte
        for i in range(10):
          cap = cv2.VideoCapture(i, cv2.CAP_ANY)  # CAP_DSHOW für bessere Performance
          if cap.isOpened():
            print(f"✅ Capture Card gefunden: ID {i}")
            found_devices.append(i)
            cap.release()

        if found_devices:
          self.device_select.addItems([f"Capture {i}" for i in found_devices])
        else:
          print("❌ Keine Capture Card gefunden!")
    

    def select_capture_device(self, index):
      device_id = int(self.device_select.currentText().split()[-1])
      print(f"🎥 Capture Card {device_id} ausgewählt!")

      # Falls schon eine Capture Card aktiv ist, freigeben
      if self.capture:
        self.capture.release()

      # Neue Capture Card starten
      self.capture = cv2.VideoCapture(device_id, cv2.CAP_ANY)
      self.timer.start(30)  # Alle 30ms neues Bild anzeigen


    def update_frame(self):
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.resize(frame, (400, 225))  # Skalieren
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Farben anpassen
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        else:
            self.timer.stop()  # Wenn kein Bild kommt, Timer stoppen



    # 🔹 Tab 4: OCR-Prozesse
    def create_log_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # 🎯 Originalbild mit erkanntem Text
        self.ocr_output_label = QLabel("📜 OCR-Result")
        self.ocr_output_label.setFixedSize(600, 338)  # Standardgröße
        layout.addWidget(self.ocr_output_label)

        # 🎯 Verarbeitetes ROI-Bild
        self.roi_output_label = QLabel("🔍 Processed-ROI")
        self.roi_output_label.setFixedSize(400, 225)  # Standardgröße
        layout.addWidget(self.roi_output_label)

        tab.setLayout(layout)
        return tab



    # Tab 5: für die Team-Tabelle hinzufügen
    def create_table_tab(self):
        tab = QWidget()

        # Layout für den neuen Tab
        layout = QVBoxLayout()

        # **Haupt-Container für die Tabelle**
        self.table_wrapper = QWidget()
        if self.vertical_layout == True:
            self.table_wrapper_layout = QVBoxLayout(self.table_wrapper)
            self.table_wrapper_layout.setSpacing(0)
        else:
            self.table_wrapper_layout = QHBoxLayout(self.table_wrapper)
        layout.addWidget(self.table_wrapper, alignment=Qt.AlignmentFlag.AlignCenter)

        # **Score-Tabelle für Teams**
        self.team_containers = {}  # Hier werden die Team-Boxen gespeichert
        for i in range(6):  # Platz für bis zu 6 Teams
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # **Obere Box mit Teams und Punktestand**
            team_box = QLabel()
            team_box.setFixedSize(80, 40)
            team_box.setStyleSheet("border-radius: 5px; font-size: 22px; text-align: center; background-color: rgba(20,20,20,50%);")
            team_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # **Untere Box mit Rennzahl und Differenz**
            bottom_box = QLabel()
            bottom_box.setFixedSize(80, 20)
            bottom_box.setStyleSheet("font-size: 17px; font-weight: bold;")
            if self.vertical_layout == True:
                bottom_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                bottom_box.setAlignment(Qt.AlignmentFlag.AlignLeft)

            if self.vertical_layout == True:
                container_layout.addWidget(bottom_box)
                container_layout.addWidget(team_box)
            else:
                container_layout.addWidget(team_box)
                container_layout.addWidget(bottom_box)
            container.setLayout(container_layout)

            self.table_wrapper_layout.addWidget(container)
            self.team_containers[i] = (team_box, bottom_box)  # Speichert die Labels


        tab.setLayout(layout)
        return tab
    

    # Tab 6: Einstellungen für das Scoreboard
    def create_table_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Initiale Booleans für die beiden Buttons
        self.show_race_count = True
        self.show_difference = True
        self.fade_in = True
        # Layout-Zustand laden
        self.load_layout_state()

        # Erster Button (Rennzähler)
        self.race_count_button = QPushButton("Racecount: On")
        self.race_count_button.setFixedSize(150, 20)
        self.race_count_button.clicked.connect(self.toggle_race_count)
        self.update_button_style(self.race_count_button, self.show_race_count)

        # Zweiter Button (Differenz)
        self.difference_button = QPushButton("Difference: On")
        self.difference_button.clicked.connect(self.toggle_difference)
        self.difference_button.setFixedSize(150, 20)
        self.update_button_style(self.difference_button, self.show_difference)

        # Buttons in den Tab einfügen
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.race_count_button)
        settings_layout.addWidget(self.difference_button)

        # Buttons ins Layout einfügen
        layout.addLayout(settings_layout)


        # Fade-In Button
        self.fade_in_button = QPushButton("Fade-In: Off")
        self.fade_in_button.setFixedSize(150, 20)
        self.fade_in_button.clicked.connect(self.toggle_fade_in)
        self.update_button_style_inverted(self.fade_in_button, self.fade_in)

        
        settings_layout2 = QHBoxLayout()
        settings_layout2.addWidget(self.fade_in_button, alignment=Qt.AlignmentFlag.AlignCenter)

            # 🏆 "Info"-Button
        fadein_info_button = QPushButton("i")
        fadein_info_button.setFixedSize(20, 20)  
        fadein_info_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                font-size: 18px;
                border-radius: 10px;  /* Runde Form */
            }
            QPushButton:pressed {
                background-color: blue;
            }
        """)
        fadein_info_button.clicked.connect(lambda: self.show_info("""
        This Setting will make the Scoreboard appear everytime it updates.
        After 60s of downtime, the Scoreboard disappears.

        Diese Einstellung lässt das Scoreboard erscheinen, wenn es aktualisiert wird.
        Nach 60s ohne Aktivität verschwindet das Scoreboard.                                                                                                                                                                              
        """))
        settings_layout2.addWidget(fadein_info_button, alignment=Qt.AlignmentFlag.AlignLeft)


        layout.addLayout(settings_layout2)


        # Vertikales Layout Button
        self.vertical_layout_button = QPushButton("Vertical Layout")
        self.vertical_layout_button.setFixedSize(150, 20)
        self.vertical_layout_button.clicked.connect(self.toggle_vertical_layout)
        self.update_button_style(self.vertical_layout_button, self.vertical_layout)

        settings_layout3 = QHBoxLayout()
        settings_layout3.addWidget(self.vertical_layout_button, alignment=Qt.AlignmentFlag.AlignCenter)


            # 🏆 "Info"-Button
        verticallayout_info_button = QPushButton("i")
        verticallayout_info_button.setFixedSize(20, 20)
        verticallayout_info_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                font-size: 18px;
                border-radius: 10px;  /* Runde Form */
            }
            QPushButton:pressed {
                background-color: blue;
            }
        """)
        verticallayout_info_button.clicked.connect(lambda: self.show_info("""
        This changes the appearance of the Scoreboard.
        You HAVE to restart the program to apply the changes.  

        Das verändert das Aussehen des Scoreboards.
        Du MUSST das Programm neu starten, um die Änderungen anzuwenden.                                                                                                                                                                                                                                                                      
        """))
        settings_layout3.addWidget(verticallayout_info_button, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout.addLayout(settings_layout3)


        tab.setLayout(layout)
        return tab
    


    def update_button_style(self, button, state):
        # Farbe und Text abhängig vom Zustand
        if state:
            button.setStyleSheet("background-color: rgb(49, 176, 64); color: white; font-size: 14px; border-radius: 5px;")
        else:
            button.setStyleSheet("background-color: rgb(136, 133, 133); color: white; font-size: 14px; border-radius: 5px;")


    def update_button_style_inverted(self, button, state):
        # Farbe und Text abhängig vom Zustand
        if state:
            button.setStyleSheet("background-color: rgb(136, 133, 133); color: white; font-size: 14px; border-radius: 5px;")
        else:
            button.setStyleSheet("background-color: rgb(49, 176, 64); color: white; font-size: 14px; border-radius: 5px;")


    def toggle_race_count(self):
        # Toggle Boolean
        self.show_race_count = not self.show_race_count
        # Text aktualisieren
        status = "On" if self.show_race_count else "Off"
        self.race_count_button.setText(f"Racecount: {status}")
        print(f"Rennzähler ist jetzt: {self.show_race_count}")
        # Style aktualisieren
        self.update_button_style(self.race_count_button, self.show_race_count)


    def toggle_difference(self):
        # Toggle Boolean
        self.show_difference = not self.show_difference
        # Text aktualisieren
        status = "On" if self.show_difference else "Off"
        self.difference_button.setText(f"Difference: {status}")
        print(f"Differenz ist jetzt: {self.show_difference}")
        # Style aktualisieren
        self.update_button_style(self.difference_button, self.show_difference)


    def toggle_fade_in(self):
        # Toggle Boolean
        self.fade_in = not self.fade_in
        self.table_wrapper.setVisible(self.fade_in)  # Sichtbarkeit des Scoreboards ändern
        # Text aktualisieren
        status = "Off" if self.fade_in else "On"
        self.fade_in_button.setText(f"Fade-In: {status}")
        print(f"Fade-In ist jetzt: {self.fade_in}")
        # Style aktualisieren
        self.update_button_style_inverted(self.fade_in_button, self.fade_in)

    def show_scoreboard_temp(self):
        """Zeigt das Scoreboard temporär nach einem Rennen."""
        if not self.fade_in:  
            self.table_wrapper.setVisible(True)

            # Falls ein Timer schon läuft, stoppen
            if hasattr(self, 'hide_timer') and self.hide_timer.isActive():
                self.hide_timer.stop()

            # Timer erstellen, wenn er nicht existiert
            if not hasattr(self, 'hide_timer'):
                self.hide_timer = QTimer()
                self.hide_timer.timeout.connect(self.hide_scoreboard)

            # Timer für 60 Sekunden starten
        self.hide_timer.start(60000)

    def hide_scoreboard(self):
        """Blendet das Scoreboard nach Ablauf des Timers aus."""
        if not self.fade_in:  # Nur verstecken, wenn nicht manuell sichtbar
            self.table_wrapper.setVisible(False)


    def toggle_vertical_layout(self):
        # Toggle Boolean
        self.vertical_layout = not self.vertical_layout
        # Text aktualisieren
        status = "On" if self.vertical_layout else "Off"
        self.vertical_layout_button.setText(f"Vertical Layout: {status}")
        print(f"Vertikales Layout ist jetzt: {self.vertical_layout}")
        # Style aktualisieren
        self.update_button_style(self.vertical_layout_button, self.vertical_layout)
        self.save_layout_state()  # Zustand speichern

    def save_layout_state(self):
        """Speichert den Zustand des Layouts in einer JSON-Datei."""
        file_path = "layout_state.json"
        state = {"vertical_layout": self.vertical_layout}
        with open(file_path, "w") as file:
            json.dump(state, file)
        print(f"💾 Layout-Zustand gespeichert: {state}")

    def load_layout_state(self):
        """Lädt den Zustand des Layouts aus einer JSON-Datei."""
        file_path = "layout_state.json"
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                try:
                    state = json.load(file)
                    self.vertical_layout = state.get("vertical_layout", False)
                    print(f"📂 Layout-Zustand geladen: {state}")
                except json.JSONDecodeError:
                    self.vertical_layout = False
                    print("⚠️ Fehler beim Laden des Layout-Zustands. Standardwert wird verwendet.")
        else:
            self.vertical_layout = False
            print("📂 Keine Layout-Zustandsdatei gefunden. Standardwert wird verwendet.")



    def check_conditions(self):
        if self.condition1 and self.condition2:
            self.start_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(False)


    # 📌 Team-Tags speichern
    def apply_team_tags(self):
        """ Speichert Team-Tags aus den Eingabefeldern. """
        if not self.selected_team_size:
            QMessageBox.warning(self, "Error", "Select Mode!")
            return

        self.team_tags = {}  # Team-Tags zurücksetzen
        num_teams = 12 // self.selected_team_size  # Anzahl Teams berechnen

        for i in range(num_teams):
            tag = self.team_tag_inputs[i].text().strip().upper()
            if tag:
                self.team_tags[i] = tag
            else:
                QMessageBox.warning(self,"Error", "Enter Every Team Tag!")
                return

        # Lade existierende Scores
        saved_scores = self.load_team_scores()

        # Setze für neue Teams die Punkte auf 0
        for team in self.team_tags.values():
            if team not in saved_scores:
                saved_scores[team] = 0
                self.save_team_scores({team: 0})  # Speichern mit 0 Punkten


        print("📌 Gespeicherte Team-Tags:", self.team_tags)
        self.condition1 = True
        self.check_conditions()
        self.update_score_table()
        self.update_score_list()



    # Bildverarbeitung
    def perform_ocr(self, frame):
        """OCR-Prozess für Spielererkennung und Teamzuweisung starten, mit visueller Ausgabe."""
        if not self.capture or not self.capture.isOpened():
            QMessageBox.warning(self,"Error", "Setup your Capture Card!")
            return

        ret, frame = self.capture.read()
        if not ret:
            QMessageBox.warning(self,"Error", "failed capturing the Frame, make sure your Capture Card is connected.")
            return

        # 🔹 Bildverarbeitung mit OpenCV
        frame_resized = cv2.resize(frame, (1200 * 2, 675 * 2))  # Einheitliche Größe setzen
        frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(frame_gray, 176, 255, cv2.THRESH_BINARY)
        #morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((1, 1), np.uint8))

        # 🔹 OCR-Bereich definieren
        start_x, width = 634 * 2, 190 * 2
        start_y, row_height = 50 * 2, 47 * 2
        num_players = 12
        placement_points = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

        players = []

        # 🎨 Originalbild-Kopie für Markierungen
        frame_annotated = frame_resized.copy()
        roi_combined = np.zeros((num_players * row_height, width), dtype=np.uint8)  # Leeres Bild für ROIs

        for i in range(num_players):
            y1 = start_y + i * (row_height + 2)
            roi = thresh[y1:y1 + row_height, start_x:start_x + width]
            
            # 🏆 OCR ausführen
            result = self.reader.readtext(roi, detail=0, text_threshold=0.3, low_text=0.2)
            #result2 = self.readerjpn.readtext(roi, detail=0, text_threshold=0.3, low_text=0.2)

            if result:
                player_name = result[0].strip()
                team_tag = self.find_team_by_name(player_name)
                points = placement_points[i]
                
                print(f"🎯 Spieler erkannt: {player_name} → {points} Punkte → Team: {team_tag}")
                players.append((player_name, team_tag, points))

                # 🔴 Bounding Box ins Originalbild zeichnen
                top_left = (start_x, y1)
                bottom_right = (start_x + width, y1 + row_height)
                cv2.rectangle(frame_annotated, top_left, bottom_right, (0, 255, 0), 2)

                # 🏷️ Erkannten Text einzeichnen
                cv2.putText(frame_annotated, player_name, (start_x + 5, y1 + row_height - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255),5)
                
                # 🔥 Alle ROIs übereinanderstapeln
                roi_combined[i * row_height:(i + 1) * row_height, :] = roi

            #elif result2:
                #player_name = result2[0].strip()
                #team_tag = self.find_team_by_name(player_name)
                #if team_tag == "0":
                #    break
                #points = placement_points[i]
                
                #print(f"🎯 Spieler erkannt: {player_name} → {points} Punkte → Team: {team_tag}")
                #players.append((player_name, team_tag, points))

                # 🔴 Bounding Box ins Originalbild zeichnen
                #top_left = (start_x, y1)
                #bottom_right = (start_x + width, y1 + row_height)
                #cv2.rectangle(frame_annotated, top_left, bottom_right, (0, 255, 0), 2)

                # 🏷️ Erkannten Text einzeichnen
                #cv2.putText(frame_annotated, player_name, (start_x + 5, y1 + row_height - 5),
                #            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255),5)
                
                # 🔥 Alle ROIs übereinanderstapeln
                #roi_combined[i * row_height:(i + 1) * row_height, :] = roi

            else:
                print(f"⚠️ Spieler an Position {i + 1} nicht erkannt!")

        # 🔹 Ergebnisse anzeigen
        self.display_image(frame_annotated, self.ocr_output_label)  # Originalbild mit Markierungen
        self.display_image(roi_combined, self.roi_output_label)  # Nur ROI-Bereich!

        # 🏆 Teamwertung berechnen, wenn Spieler erkannt wurden
        if players:
            self.calculate_team_scores(players)
            self.increment_race_count()
            self.update_score_table()
            self.update_score_list()
        else:
            print("⚠️ Keine Spieler erkannt!")

        
    def display_image(self, image, label):
        """Zeigt ein OpenCV-Bild in einem QLabel an."""
        if len(image.shape) == 2:  # Graustufenbild
            format = QImage.Format.Format_Grayscale8
            bytes_per_line = image.shape[1]
        else:  # Farbimage (BGR → RGB konvertieren)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            format = QImage.Format.Format_RGB888
            bytes_per_line = 3 * image.shape[1]

        h, w = image.shape[:2]
        q_image = QImage(image.data, w, h, bytes_per_line, format)
        pixmap = QPixmap.fromImage(q_image)

        # 📏 Skaliert das Bild auf die Größe des QLabel
        label.setPixmap(pixmap.scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio))


    # def extract_roi(self, frame):
        #"""Extrahiert den relevanten OCR-Bereich (Spielernamen) für eine separate Verarbeitung."""
        #roi_x, roi_y, roi_width, roi_height = 633, 51, 179, 440  # Diese Werte anpassen!

        #roi = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width].copy()
        
        # 🖤 Graustufen & Kontrast anpassen
        #gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        #_, thresh = cv2.threshold(gray, 192, 255, cv2.THRESH_BINARY)

        #return thresh 


   

    def calculate_team_scores(self, players):
        """Berechnet die Punkte pro Team und speichert sie."""
        team_scores = {}

        for player_name, team_tag, points in players:
            if team_tag not in team_scores:
                team_scores[team_tag] = 0
            team_scores[team_tag] += points  # Punkte für das Team addieren

        print(f"🏆 Finale Team-Ergebnisse dieses Rennens: {team_scores}")

        self.save_team_scores(team_scores)  # Speichern der Ergebnisse
        self.load_team_scores()  # UI aktualisieren



    def save_team_scores(self, team_scores):
        """Speichert die Team-Punkte in einer JSON-Datei."""
        file_path = "team_scores.json"

        # Falls Datei existiert, lade bestehende Daten
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                saved_scores = json.load(file)
        else:
            saved_scores = {}

        # Addiere die neuen Punkte
        for team, points in team_scores.items():
            if team not in saved_scores:
                saved_scores[team] = 0
            saved_scores[team] += points

        # Speichern in JSON-Datei
        with open(file_path, "w") as file:
            json.dump(saved_scores, file)

        print(f"💾 Team-Punkte gespeichert: {saved_scores}")


    def load_team_scores(self):
        """Lädt die gespeicherten Team-Punkte und zeigt sie im UI an."""
        file_path = "team_scores.json"

        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                saved_scores = json.load(file)
        else:
            saved_scores = {}

        print(f"📊 Gesamte Punktetabelle: {saved_scores}")

        return saved_scores


    def increment_race_count(self):
        """Erhöht den Rennenzähler um 1 und speichert den neuen Wert in einer JSON-Datei."""
        file_path = "race_count.json"
        # Lade den aktuellen Wert, falls vorhanden
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                try:
                    data = json.load(file)
                    race_count = data.get("race_count", 0)
                except json.JSONDecodeError:
                    race_count = 0
        else:
            race_count = 0

        race_count += 1  # Zähler erhöhen

        with open(file_path, "w") as file:
            json.dump({"race_count": race_count}, file)

        print(f"Rennenzähler erhöht: {race_count}")


    def load_race_count(self):
        races = "race_count.json"
        if os.path.exists(races):
            with open(races, "r") as file:
                try:
                    data = json.load(file)
                    race_count = data.get("race_count")
                    return race_count
                except:
                    return 0
        return 0


    # 🛠 Team-Punkte zurücksetzen und Automatik stoppen
    def reset_scores(self):
        """Löscht die gespeicherten Team-Punkte."""
        scores = "team_scores.json"

        if os.path.exists(scores):
            os.remove(scores)  # Datei löschen

        print("🗑️ Team-Punkte zurückgesetzt!")
        self.load_team_scores()  # UI aktualisieren
        self.is_ocr_running = False
        self.start_btn.setText("🔄 START")
        self.condition1 = False
        self.check_conditions()
        print("⛔ OCR-Prüfung gestoppt.")
        self.team_tags = {}  # Team-Tags zurücksetzen
        self.update_score_table() 
        self.update_score_list() 


    def reset_race_count(self):
        """Setzt den Rennenzähler auf 0 und speichert den Wert in der JSON-Datei."""
        file_path = "race_count.json"
        with open(file_path, "w") as file:
            json.dump({"race_count": 0}, file)
        print("Rennenzähler zurückgesetzt auf 0")
        self.update_score_list()


    # Manuelle OCR-Auslösung
    def capture_image_for_ocr(self):
        """Nimmt ein Bild von der Capture Card auf und führt OCR aus."""
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                # 🎨 Farben konvertieren (von BGR zu RGB)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 📷 In ein QImage umwandeln
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

                # 🖼️ Vorschau im Video-Label anzeigen
                self.video_label.setPixmap(QPixmap.fromImage(qt_image))

                # 🏆 OCR ausführen (Nutzung von EasyOCR)
                self.perform_ocr(frame)

            else:
                print("❌ Fehler beim Erfassen des Bildes!")
                QMessageBox.warning(self,"Error", "Failed Capturing Image!")
        else:
            print("❌ Keine aktive Capture Card gefunden!")
            QMessageBox.warning(self,"Error", "No Active Capture Card!")


    def find_team_by_name(self, player_name):
        """Findet das zugehörige Team anhand des Spielernamens, aber nur, wenn der Team-Tag am Anfang oder Ende steht."""
        player_name = player_name.strip().upper()  # Namen bereinigen und in Kleinbuchstaben umwandeln

        for team_tag in self.team_tags.values():
            team_tag = team_tag.upper()

            if player_name.startswith(team_tag):
                return team_tag  # Nur zuordnen, wenn der Tag am Anfang steht
            
            elif player_name.endswith(team_tag):
                return team_tag  # Nur zuordnen, wenn der Tag am Ende steht
        
        return "Missing"  # Falls kein passendes Team gefunden wurde
    

    def update_score_table(self):
        """
        Aktualisiert die Team-Tabelle im vierten Tab.
        Die Anzeige basiert direkt auf den eingegebenen Team-Tags, sodass sich
        die Zahl der angezeigten Teams nicht verändert, wenn z. B. OCR fehl schlägt.
        """
        # Kapitel 1: Daten laden
        saved_scores = self.load_team_scores()
        race_count = self.load_race_count()
        valid_teams = self.get_defined_teams()  # Nur definierte Teams zulassen

        self.show_scoreboard_temp()  # Zeige Scoreboard temporär an

        print("Definierte Teams",valid_teams)

        # Teams filtern (nur definierte Teams behalten)
        filtered_scores = {team: points for team, points in saved_scores.items() if team in valid_teams}
        print("🔍 Gefilterte Team-Punkte:", filtered_scores)

        # Falls kein einziges gültiges Team übrig bleibt, breche ab
        if not filtered_scores:
            print("⚠️ Keine gültigen Teams gefunden. Tabelle bleibt leer.")
            return

        # Kapitel 2: Sortiere Teams und bestimme Hauptteam
        sorted_teams = self.get_sorted_teams(filtered_scores)
        main_team = self.get_main_team()

        # Kapitel 3: Aktualisiere die UI-Elemente (wir gehen von 6 Container aus)
        # Wir iterieren über 6 Container, auch wenn es weniger Teams gibt.
        for i in range(6):
            team_box, bottom_box = self.team_containers[i]
            if i < len(sorted_teams):
                team_name, team_points = sorted_teams[i]
                team_box.setText(f"{team_name} {team_points}")  # Concatenate team name and points
                # Wenn das Team-Tag dem Hauptteam entspricht, wende den Gold-Stil an.
                if team_name == main_team:
                    team_box.setStyleSheet("border-radius: 5px; font-size: 22px; color: gold; background-color: rgba(20,20,20,50%);")
                else:
                    team_box.setStyleSheet("border-radius: 5px; font-size: 22px; color: rgb(240,240,240); background-color: rgba(20,20,20,50%);")
                # Untere Box: Für das erste Team zeige Rennen, sonst Differenz zum vorherigen Team
                if i == 0:
                    if self.show_race_count == True:
                        bottom_box.setText(f"Races: {race_count}")
                        bottom_box.setStyleSheet("color: #c23fd9; font-size: 17px; font-weight: bold;")
                    else:
                        bottom_box.setText("")
                        bottom_box.setStyleSheet("color: rgba(0,0,0,0%); font-size: 17px; font-weight: bold;")
                else:
                    diff = sorted_teams[i-1][1] - team_points
                    if self.show_difference == True:
                        bottom_box.setText(f"-{diff}")
                        bottom_box.setStyleSheet("color: rgb(252,55,55); font-size: 17px; font-weight: bold; background-color: rgba(20,20,20,50%);")
                    else:
                        bottom_box.setText("")
                        bottom_box.setStyleSheet("color: rgba(0,0,0,0%); font-size: 17px; font-weight: bold;")
            else:
                # Falls weniger Teams als Container vorhanden sind, leere die restlichen Container
                team_box.setText("")
                team_box.setStyleSheet("background-color: rgba(0,0,0,0%);")
                bottom_box.setText("")


    def get_defined_teams(self):
        """
        Gibt die Liste der gültigen Teams zurück, die in den Eingaben definiert wurden.
        """
        return self.team_tags.values()
    

    def get_sorted_teams(self, saved_scores):
        # Sortiere saved_scores (Dictionary) nach Punkten absteigend
        sorted_teams = sorted(saved_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_teams


    def get_main_team(self):
        # Nimm an, dass self.team_tags bereits gesetzt wurde
        if hasattr(self, "team_tags") and self.team_tags:
            # Das erste eingegebene Team
            return list(self.team_tags.values())[0]
        return None
    
    
    def toggle_ocr(self):
        if not self.is_ocr_running:
            self.is_ocr_running = True
            self.start_btn.setText("⏹ STOP")
            print("✅ OCR-Prüfung gestartet.")
            self.start_check_loop()  # Startet den Loop
        else:
            self.is_ocr_running = False
            self.start_btn.setText("🔄 START")
            print("⛔ OCR-Prüfung gestoppt.")


    def start_check_loop(self):
        # Diese Methode ruft sich alle 1 Sekunde selbst wieder auf
        if not self.is_ocr_running or self.is_paused:
            return
        self.capture_and_process_image()
        QTimer.singleShot(800, self.start_check_loop)


    def capture_and_process_image(self):
        if self.is_paused:
            return
        print("📸 Bild wird verarbeitet...")

        # Lese ein Frame von der Capture Card (vorausgesetzt, self.capture wurde bereits initialisiert)
        ret, frame = self.capture.read()
        if not ret:
            print("❌ Fehler beim Einlesen des Frames!")
            return

        # Skaliere das Bild auf 1200 x 675
        frame_resized = cv2.resize(frame, (1200, 675))
        
        # Definiere den Prüfbereich (ROI)
        areaX, areaY, areaWidth, areaHeight = 521, 584, 60, 40
        # Beachte: Diese Werte sind in Pixeln im skalierten Bild!
        roi = frame_resized[areaY:areaY+areaHeight, areaX:areaX+areaWidth].copy()

        # Optional: Zeige den ROI in einem Vorschau-Label (sofern vorhanden)
        if hasattr(self, "preview_label") and self.preview_label is not None:
            self.display_image(roi, self.preview_label)

        # OpenCV-Verarbeitung (entspricht sampleProcess)
        processed_roi = self.sample_process(roi)

        # OCR-Prüfung für den ROI
        is_valid = self.perform_check_ocr(processed_roi)
        if is_valid:
            print("✅ Scoreboard erkannt! Starte OCR...")
            self.is_paused = True  # Pause den Prüf-Loop
            # Übergib das ganze Bild (frame_resized) an die OCR-Funktion
            self.perform_ocr(frame_resized)
            # Nach 90 (120) Sekunden den Loop wieder aktivieren:
            QTimer.singleShot(120000, self.resume_check_loop)
        else:
            print("❌ Kein Scoreboard erkannt, Bild verworfen.")

    
    def perform_check_ocr(self, processed_roi):
        detected_text = self.sample_text(processed_roi)
        print("OCR-Ergebnis für Prüfung:", detected_text)
        return "12" in detected_text


    def sample_text(self, image):
        # image ist ein numpy-Array (z. B. das von sample_process verarbeitete ROI)
        #reader = easyocr.Reader(["en"])  # Alternativ: Du kannst den Reader auch global einmal initialisieren
        result = self.reader.readtext(image, detail=0)
        detected_text = " ".join([text for text in result])
        return detected_text.strip()


    def sample_process(self, roi):
        # roi: numpy-Array (ROI-Bereich)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape)==3 else roi.copy()
        _, thresh = cv2.threshold(gray, 175, 255, cv2.THRESH_BINARY)
        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        # closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        # blurred = cv2.GaussianBlur(closed, (3, 3), 0)
        return thresh


    def resume_check_loop(self):
        print("⏳ Cooldown vorbei, OCR-Loop startet erneut.")
        self.is_paused = False
        if self.is_ocr_running:
            self.start_check_loop()


    def update_score_list(self):
        """ Erstellt die Liste mit Teams, Punkten und Buttons zum Anpassen. """
        # Lade die Daten
        saved_scores = self.load_team_scores()  # Holt die Team-Scores aus der JSON
        races_done = self.load_race_count()  # Holt die Anzahl der Rennen

        # Liste oder Textfeld zuerst **leeren**, damit keine alten Daten bleiben!
        self.score_list_widget.clear()  # Falls du ein QListWidget nutzt
        # self.score_textedit.clear()  # Falls du ein QTextEdit nutzt

        # Füge die Rennanzahl als ersten Eintrag hinzu
        self.score_list_widget.addItem(f"Races: {races_done}")

        # 🔹 Erwartete Punkte = Anzahl der Rennen * 82
        expected_points = races_done * 82
        actual_points = sum(saved_scores.values())  # 🔹 Tatsächlich vergebene Punkte

        for team, points in saved_scores.items():
            # Widget für den Listeneintrag
            item_widget = QWidget()
            layout = QHBoxLayout(item_widget)

            # Label für den Teamnamen & aktuelle Punktzahl
            label = QLabel(f"{team}: {points} Points")

            # Plus-Button (zum Punkte erhöhen)
            plus_button = QPushButton("+")
            plus_button.setFixedSize(30, 20)
            plus_button.setStyleSheet("background-color: green; color: white;")
            plus_button.clicked.connect(lambda _, t=team: self.adjust_team_score(t, 1))

            # Minus-Button (zum Punkte verringern)
            minus_button = QPushButton("-")
            minus_button.setFixedSize(30, 20)
            minus_button.setStyleSheet("background-color: red; color: white;")
            minus_button.clicked.connect(lambda _, t=team: self.adjust_team_score(t, -1))

            # Elemente anordnen
            layout.addWidget(label)
            layout.addWidget(plus_button)
            layout.addWidget(minus_button)
            layout.setContentsMargins(0, 0, 0, 0)
            item_widget.setLayout(layout)

            # Widget zur Liste hinzufügen
            list_item = QListWidgetItem()
            self.score_list_widget.addItem(list_item)
            self.score_list_widget.setItemWidget(list_item, item_widget)

        # 🔹 Punktdifferenz berechnen
        point_difference = actual_points - expected_points


        # 🔹 Falls Differenz ≠ 0, Fehleranzeige hinzufügen
        if point_difference != 0:
            diff_item = QListWidgetItem()
            diff_label = QLabel(f"⚠ Points Issue: {point_difference} Points")
            
            # 🔹 Design anpassen (optional)
            diff_label.setStyleSheet("color: red; font-weight: bold;")

            self.score_list_widget.addItem(diff_item)
            self.score_list_widget.setItemWidget(diff_item, diff_label)
    


    def adjust_team_score(self, team, amount):
        """ Erhöht oder verringert die Punkte eines Teams und speichert die Änderung. """
        saved_scores = self.load_team_scores()
        
        if team in saved_scores:
            saved_scores[team] += amount  # Punkte anpassen
            self.save_adjusted_team_scores(saved_scores)  # Speichern
            self.update_score_list()  # Liste aktualisieren
            self.update_score_table()  # Tabelle ebenfalls updaten


    def save_adjusted_team_scores(self, scores):
        """ Speichert die aktuellen Punktzahlen in die JSON-Datei. """
        with open("team_scores.json", "w") as file:
            json.dump(scores, file, indent=4)


    # Info Buttons
    def show_info(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Info")
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()






class ScoreboardWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scoreboard OBS Cleanfeed")

        # **Größe des Fensters anpassen**
        self.setFixedSize(700, 580)  # Größe der Tabelle

        # **Hintergrundfarbe setzen (z. B. grelles Grün für Chroma Key)**
        #self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Transparenz aktivieren
        #self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Randloses Fenster

        # **Hintergrundfarbe auf Grün setzen (wird später entfernt mit Chroma Key)**
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 255, 0, 150))  # Helles Grün
        self.setPalette(palette)

        # **Layout für die Tabelle**
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_table_widget(self, table_widget):
        """Setzt die Score-Tabelle ins Fenster."""
        self.layout.addWidget(table_widget)






# 🌟 App starten
app = QApplication(sys.argv)
window = OCRApp()
window.show()
sys.exit(app.exec())
