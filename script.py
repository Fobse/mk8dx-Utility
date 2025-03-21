import cv2
import easyocr
import numpy as np
import sys
import json
import os
from PyQt6.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QHBoxLayout, QComboBox, QLineEdit, QMessageBox, QListWidget
from PyQt6.QtGui import QPixmap, QImage, QPalette, QColor
from PyQt6.QtCore import QTimer, Qt


class OCRApp(QWidget):
    def __init__(self):
        super().__init__()

        # 🔵 EasyOCR Reader einmalig initialisieren
        self.reader = easyocr.Reader(["en"])
        self.readerjpn = easyocr.Reader(["ja"])

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
        self.tabs.addTab(self.create_video_tab(), "Video-Setup")
        self.tabs.addTab(self.create_log_tab(), "OCR-Process")
        self.tabs.addTab(self.create_table_tab(), "Table")

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
            btn.setFixedSize(100, 40)  # Breite 120px, Höhe 40px
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

        # 🏆 "Tags speichern"-Button
        self.apply_tags_btn = QPushButton("Apply Team-Tags")
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
        self.apply_tags_btn.clicked.connect(self.apply_team_tags)
        layout.addWidget(self.apply_tags_btn)

        # Start- und Reset-Buttons
        self.start_btn = QPushButton("Start")
        self.reset_btn = QPushButton("Reset")

        # Start-Button Styling & Standardmäßig deaktiviert
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

        # Reset Button Einstellungen
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

        # 🟢 Manueller OCR-Button
        self.manual_ocr_btn = QPushButton("Manual Trigger")
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
        self.manual_ocr_btn.clicked.connect(self.capture_image_for_ocr)


        # Buttons ins Layout setzen
        layout.addWidget(self.start_btn)
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.manual_ocr_btn)

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



    # 🔹 Tab 2: Video-Setup
    def create_video_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

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
        layout.addWidget(self.capture_btn)

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



    # 🔹 Tab 3: OCR-Prozesse
    def create_log_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

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


    def create_table_tab(self):
        # Tab 4 für die Team-Tabelle hinzufügen
        tab = QWidget()

        # Layout für den neuen Tab
        layout = QVBoxLayout()

        # **Haupt-Container für die Tabelle**
        self.table_wrapper = QWidget()
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
            bottom_box.setStyleSheet("font-size: 17px; font-weight: bold; text-align: left;")
            bottom_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

            container_layout.addWidget(team_box)
            container_layout.addWidget(bottom_box)
            container.setLayout(container_layout)

            self.table_wrapper_layout.addWidget(container)
            self.team_containers[i] = (team_box, bottom_box)  # Speichert die Labels


        tab.setLayout(layout)
        return tab



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
            tag = self.team_tag_inputs[i].text().strip()
            if tag:
                self.team_tags[i] = tag
            else:
                QMessageBox.warning(self,"Error", "Enter Every Team Tag!")
                return

        print("📌 Gespeicherte Team-Tags:", self.team_tags)
        self.condition1 = True
        self.check_conditions()



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
        _, thresh = cv2.threshold(frame_gray, 175, 255, cv2.THRESH_BINARY)
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



    #def find_team_by_name(self, player_name):
     #   """Sucht nach einem gespeicherten Team-Tag basierend auf dem Spielernamen."""
      #  for team_id, tag in self.team_tags.items():
       #     if tag.upper() in player_name.upper():
        #        return tag
        #return "Unbekannt"
    

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

        # 🔹 Ergebnisse nach Punkten sortieren (höchste zuerst)
        sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)

        # 🏆 Ergebnisse anzeigen
        self.display_team_scores(sorted_teams)


    def display_team_scores(self, sorted_teams):
        """Zeigt die berechneten Team-Punkte in der OCR-Log-Tabelle an."""
        self.log_text.clear()
        self.log_text.append("\n🏆 Teamwertung: ")
        for rank, (team, points) in enumerate(sorted_teams, start=1):
            self.log_text.append(f"{rank}. {team}: {points} Punkte")


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
        # Optional: Aktualisiere ein UI-Element, z.B. ein Label:
        #if hasattr(self, "race_count_label"):
            #self.race_count_label.setText(f"Rennen: {race_count}")


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


    def reset_race_count(self):
        """Setzt den Rennenzähler auf 0 und speichert den Wert in der JSON-Datei."""
        file_path = "race_count.json"
        with open(file_path, "w") as file:
            json.dump({"race_count": 0}, file)
        print("Rennenzähler zurückgesetzt auf 0")
        # Optional: UI-Element aktualisieren
        #if hasattr(self, "race_count_label"):
            #self.race_count_label.setText("Rennen: 0")

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
        
        return "unbekannt"  # Falls kein passendes Team gefunden wurde
    

    def update_score_table(self):
        """
        Aktualisiert die Team-Tabelle im vierten Tab.
        Die Anzeige basiert direkt auf den eingegebenen Team-Tags, sodass sich
        die Zahl der angezeigten Teams nicht verändert, wenn z. B. OCR fehl schlägt.
        """
        # Kapitel 1: Daten laden
        saved_scores = self.load_team_scores()
        race_count = self.load_race_count()

        # Falls keine Daten vorhanden sind, setze Standardanzeige
        #if not saved_scores:
            #for container in self.team_containers.values():
                #team_box, bottom_box = container
                #team_box.setText("0")
                #bottom_box.setText("")
            #return

        # Kapitel 2: Sortiere Teams und bestimme Hauptteam
        sorted_teams = self.get_sorted_teams(saved_scores)
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
                    team_box.setStyleSheet("border-radius: 5px; font-size: 26px; color: gold; text-align: center; background-color: rgba(20,20,20,50%);")
                else:
                    team_box.setStyleSheet("border-radius: 5px; font-size: 26px; color: rgb(240,240,240); text-align: center; background-color: rgba(20,20,20,50%);")
                # Untere Box: Für das erste Team zeige Rennen, sonst Differenz zum vorherigen Team
                if i == 0:
                    bottom_box.setText(f"Races: {race_count}")
                    bottom_box.setStyleSheet("color: #c23fd9; font-weight: bold; font-size: 17px; text-align: left;")
                else:
                    diff = sorted_teams[i-1][1] - team_points
                    bottom_box.setText(f"-{diff}")
                    bottom_box.setStyleSheet("color: rgb(252,55,55); font-size: 17px; text-align: left;")
            else:
                # Falls weniger Teams als Container vorhanden sind, leere die restlichen Container
                team_box.setText("")
                team_box.setStyleSheet("background-color: rgba(0,0,0,0%);")
                bottom_box.setText("")


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
        QTimer.singleShot(1000, self.start_check_loop)


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






class ScoreboardWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scoreboard OBS Cleanfeed")

        # **Größe des Fensters anpassen**
        self.setFixedSize(800, 300)  # Größe der Tabelle

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
