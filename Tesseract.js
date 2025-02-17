function performOCR() {
    let fileInput = document.getElementById("imageInput");
    let playerList = document.getElementById("playerList");
    let teamScoresList = document.getElementById("teamScores");

    playerList.innerHTML = ""; // Alte Werte löschen
    teamScoresList.innerHTML = "";

    if (fileInput.files.length === 0) {
        alert("Bitte ein Bild hochladen!");
        return;
    }

    let file = fileInput.files[0];
    let reader = new FileReader();

    reader.onload = function () {
        let img = new Image();
        img.src = reader.result;

        img.onload = function () {
            Tesseract.recognize(
                img,
                'eng', // Sprache: 'eng' oder 'deu' falls nötig
                { logger: m => console.log(m) } // Fortschritt in der Konsole sehen
            ).then(({ data: { text } }) => {
                let lines = text.split("\n").filter(line => line.trim() !== ""); // Leere Zeilen entfernen
                
                // Punkte-Tabelle für Platzierungen
                let placementPoints = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1];

                let teamScores = {}; // Speichert die Gesamtpunkte pro Team
                
                lines.forEach((player, index) => {
                    if (index < placementPoints.length) { // Nur die ersten 12 Spieler zählen
                        let cleanName = player.trim();
                        let points = placementPoints[index];

                        // Erster Buchstabe des Namens als Team-Tag
                        let teamTag = cleanName[0];

                        // Punkte zum Team addieren
                        if (!teamScores[teamTag]) {
                            teamScores[teamTag] = 0;
                        }
                        teamScores[teamTag] += points;

                        // Spieler-Liste in HTML ausgeben
                        let li = document.createElement("li");
                        li.textContent = `${cleanName} → ${points} Punkte`;
                        playerList.appendChild(li);
                    }
                });

                // Team-Ergebnisse anzeigen
                for (let team in teamScores) {
                    let li = document.createElement("li");
                    li.textContent = `Team ${team}: ${teamScores[team]} Punkte`;
                    teamScoresList.appendChild(li);
                }
            }).catch(err => {
                console.error("Fehler bei der Texterkennung:", err);
            });
        };
    };

    reader.readAsDataURL(file);
}
