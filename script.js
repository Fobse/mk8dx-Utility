function resizeImage(src, maxWidth) {
    let dst = new cv.Mat();
    let scale = maxWidth / src.cols;
    let newSize = new cv.Size(src.cols * scale, src.rows * scale);
    cv.resize(src, dst, newSize, 0, 0, cv.INTER_AREA);
    return dst;
}
let selectedTeamSize = null;
let teamTags = {}; // Speichert die Team-Tags

// 🏆 1️⃣ Teamgröße setzen & Eingabefelder generieren
function setTeamSize(size) {
    selectedTeamSize = size;
    let inputContainer = document.getElementById("teamTagInputs");
    inputContainer.innerHTML = ""; // Vorherige Eingaben löschen

    for (let i = 0; i < 12 / size; i++) {
        let input = document.createElement("input");
        input.type = "text";
        input.placeholder = `Team ${i + 1} Tag`;
        input.id = `teamTag_${i}`;
        inputContainer.appendChild(input);
    }
    
    console.log(`✅ Teamgröße ${size} ausgewählt!`);
}

// 🏆 2️⃣ Team-Tags aus Eingaben speichern
function applyTeamTags() {
    if (!selectedTeamSize) {
        alert("Select Mode First!");
        return;
    }

    teamTags = {};
    let numTeams = 12 / selectedTeamSize;

    for (let i = 0; i < numTeams; i++) {
        let tag = document.getElementById(`teamTag_${i}`).value.trim();
        if (tag) {
            teamTags[i] = tag;
        } else {
            alert("Fill In all Team-Tags!");
            return;
        }
    }

    console.log("📌 Gespeicherte Team-Tags:", teamTags);
}


// 🏆 Teamzuweisung nach Name (anstatt nur nach Platzierung!)
async function performOCR(imageData) {
    // let fileInput = document.getElementById("imageInput");
    let playerList = document.getElementById("playerList");
    let teamScoresList = document.getElementById("teamScores");
    let resizedCanvas = document.getElementById("resizedCanvas");
    let processedRoiCanvas = document.getElementById("processedRoiCanvas");
    let resizedCtx = resizedCanvas.getContext("2d");
    let processedRoiCtx = processedRoiCanvas.getContext("2d");

    playerList.innerHTML = "";
    // teamScoresList.innerHTML = "";

   // if (fileInput.files.length === 0) {
     //   alert("Bitte ein Bild hochladen!");
       // return;
    // }

    console.log("🚀 OCR-Analyse gestartet...");

   // let file = fileInput.files[0];
    // let reader = new FileReader();

   // reader.onload = function () {
       let img = new Image();
       img.src = imageData;

       img.onload = async function () {
            let resized = cv.imread(img);
            // let resized = resizeImage(src, 1200);

           // resizedCanvas.width = resized.cols;
           // resizedCanvas.height = resized.rows;
           cv.imshow(resizedCanvas, resized);

            let gray = new cv.Mat();
            let blurred = new cv.Mat();
            let thresh = new cv.Mat();
            let morph = new cv.Mat();

            cv.cvtColor(resized, gray, cv.COLOR_RGBA2GRAY, 0);
            cv.GaussianBlur(gray, morph, new cv.Size(3, 3), 0, 0, cv.BORDER_DEFAULT);
            cv.threshold(morph, thresh, 175, 255, cv.THRESH_BINARY_INV);
            cv.morphologyEx(thresh, blurred, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(1, 1)));

            let scale = 1200 / 1920;
            let startX = 1013 * scale;
            let width = 287 * scale;
            let startY = 72 * scale;
            let rowHeight = 78 * scale;
            let numPlayers = 12;
            let placementPoints = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1];

            processedRoiCanvas.width = width;
            processedRoiCanvas.height = numPlayers * rowHeight;

            console.log("🔎 Team-Tags gespeichert:", teamTags);

            let players = [];
            let ocrPromises = [];

            for (let i = 0; i < numPlayers; i++) {
                let y1 = startY + i * rowHeight;
                let roi = blurred.roi(new cv.Rect(startX, y1, width, rowHeight));

                resizedCtx.strokeStyle = "red";
                resizedCtx.lineWidth = 2;
                resizedCtx.strokeRect(startX, y1, width, rowHeight);

                let roiCanvasTemp = document.createElement("canvas");
                roiCanvasTemp.width = width;
                roiCanvasTemp.height = rowHeight;
                let roiCtxTemp = roiCanvasTemp.getContext("2d");
                cv.imshow(roiCanvasTemp, roi);
                processedRoiCtx.drawImage(roiCanvasTemp, 0, i * rowHeight, width, rowHeight);

                let ocrPromise = Tesseract.recognize(
                    roiCanvasTemp.toDataURL(),
                    'eng',
                    {
                        logger: m => console.log(m),
                        tessedit_pageseg_mode: 'PSM_SINGLE_LINE',
                        tessedit_char_whitelist: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                    }
                ).then(({ data: { text } }) => {
                    let cleanName = text.trim();
                    if (cleanName) {
                        let points = placementPoints[i];

                        // 🏆 Hier kommt der Fix: Team-Tag wird über den Namen ermittelt!
                        let teamTag = findTeamByName(cleanName);

                        console.log(`🎯 Spieler erkannt: ${cleanName} → ${points} Punkte → Team: ${teamTag}`);

                        players.push({ name: cleanName, teamTag, points });

                        let li = document.createElement("li");
                        li.textContent = `${cleanName} → ${points} Punkte (${teamTag})`;
                        playerList.appendChild(li);

                        resizedCtx.fillStyle = "yellow";
                        resizedCtx.font = "20px Arial";
                        resizedCtx.fillText(cleanName, startX + 5, y1 + rowHeight - 10);
                    } else {
                        console.warn(`⚠️ Spieler an Position ${i + 1} wurde nicht erkannt!`);
                    }
                });

                ocrPromises.push(ocrPromise);
                roi.delete();
            }

            await Promise.all(ocrPromises);

            if (players.length > 0) {
                calculateTeamScores(players, teamScoresList);
            } else {
                console.warn("⚠️ Keine Spieler erkannt!");
            }

            // src.delete();
            resized.delete();
            gray.delete();
            blurred.delete();
            thresh.delete();
            morph.delete();
        };
    // };

    // reader.readAsDataURL(file);
}

// 🏆 **Neue Funktion: Finde das richtige Team anhand des Spielernamens**
function findTeamByName(playerName) {
    for (let teamIndex in teamTags) {
        let teamTag = teamTags[teamIndex];

        // Wenn der Name den Team-Tag enthält → Gehört zu diesem Team
        if (playerName.includes(teamTag)) {
            return teamTag;
        }
    }

    return "Unbekannt"; // Falls kein Team-Tag passt
}

function calculateTeamScores(players, teamScoresList) {
    let teamScores = {};

    for (let player of players) {
        if (!teamScores[player.teamTag]) {
            teamScores[player.teamTag] = 0;
        }
        teamScores[player.teamTag] += player.points;
    }

    console.log("🏆 Finale Team-Ergebnisse dieses Rennens:", teamScores);

    // Speichern der Ergebnisse
    saveTeamScores(teamScores);

    // Aktualisierte Gesamtpunkte anzeigen
    loadTeamScores();
}
// 🏆 **Speicherung der Team-Punkte über mehrere Rennen**
function saveTeamScores(teamScores) {
    let savedScores = JSON.parse(localStorage.getItem("teamScores")) || {};

    for (let team in teamScores) {
        if (!savedScores[team]) {
            savedScores[team] = 0;
        }
        savedScores[team] += teamScores[team];
    }

    localStorage.setItem("teamScores", JSON.stringify(savedScores));
    console.log("💾 Team-Punkte gespeichert:", savedScores);

    incrementRaceCount(); // **Neues Rennen zählen**
}


// 🏆 **Lade und zeige die Gesamtpunktzahl**
function loadTeamScores() {
    let savedScores = JSON.parse(localStorage.getItem("teamScores")) || {};
    let totalScoresList = document.getElementById("totalScores");
    
    totalScoresList.innerHTML = "";
    console.log("📊 Gesamte Punktetabelle:", savedScores);

    for (let team in savedScores) {
        let li = document.createElement("li");
        li.textContent = `Team ${team}: ${savedScores[team]} Punkte`;
        totalScoresList.appendChild(li);
    }
}

// 🏆 **Setze Punkte zurück (falls neue Runde beginnt)**
function resetTeamScores() {
    localStorage.removeItem("teamScores");
    console.log("🗑️ Team-Punkte zurückgesetzt!");
    loadTeamScores();
}

function updateScoreTable() {
    let savedScores = JSON.parse(localStorage.getItem("teamScores")) || {};
    let scoreTable = document.getElementById("scoreTable");
    let raceCountElement = document.getElementById("raceCount");

    if (Object.keys(savedScores).length === 0) {
        scoreTable.innerHTML = "<p>Empty Scores!</p>";
        return;
    }

    // Punkte sortieren (höchste zuerst)
    let sortedTeams = Object.entries(savedScores).sort((a, b) => b[1] - a[1]);

     // **Hauptteam bestimmen (das zuerst eingegebene Team)**
     let mainTeam = Object.keys(teamTags)[0];  // Team 1 ist das erste eingegebene Team

     // Rennen-Anzahl abrufen
    let racesDone = parseInt(localStorage.getItem("raceCount")) || 0;

    // **Tabelle neu aufbauen**
    scoreTable.innerHTML = ""; // Alte Tabelle löschen

    let tableWrapper = document.createElement("div");
    tableWrapper.classList.add("table-wrapper");

    sortedTeams.forEach((team, index) => {
        let teamName = team[0];
        let teamPoints = team[1];

        // **Team-Spalte erstellen**
        let teamColumn = document.createElement("div");
        teamColumn.classList.add("team-column");

         // ⭐ Falls Team-Tag "1", goldene Klasse hinzufügen
         if (teamName === teamTags[mainTeam]) {
            teamColumn.classList.add("team-gold"); // Team 1 gold färben
        }
        let nameDiv = document.createElement("div");
        nameDiv.classList.add("team-name");
        nameDiv.textContent = teamName;

        let pointsDiv = document.createElement("div");
        pointsDiv.classList.add("team-score");
        pointsDiv.textContent = teamPoints;

        teamColumn.appendChild(nameDiv);
        teamColumn.appendChild(pointsDiv);

        // **Untere Box für Rennen/Differenzen**
        let bottomBox = document.createElement("div");
        bottomBox.classList.add("bottom-box");

        if (index === 0) {
            bottomBox.textContent = `Races: ${racesDone}`; // Erste Box zeigt die Anzahl Rennen
            bottomBox.classList.add("race-count"); 
        } else {
            let diff = sortedTeams[index - 1][1] - teamPoints;
            bottomBox.textContent = `-${diff}`;
            bottomBox.classList.add("score-diff");
        }

        // Alles ins Wrapper-Div packen
        let teamContainer = document.createElement("div");
        teamContainer.classList.add("team-container");
        teamContainer.appendChild(teamColumn);
        teamContainer.appendChild(bottomBox);

        tableWrapper.appendChild(teamContainer);
    });

    scoreTable.appendChild(tableWrapper);
}


// 🏆 Rennen zählen (nach jedem OCR-Lauf)
function incrementRaceCount() {
    let racesDone = parseInt(localStorage.getItem("raceCount")) || 0;
    racesDone++;
    localStorage.setItem("raceCount", racesDone);
    updateScoreTable();
}

// Zurücksetzen der Rennen 
function resetRaceCount() {
    localStorage.removeItem("raceCount");
    console.log("🗑️ Rennen zurückgesetzt!");
    updateScoreTable();
}

// 🏆 Zurücksetzen der Punkte UND Rennen
function resetScoresAndRaces() {
    localStorage.removeItem("teamScores");
    localStorage.removeItem("raceCount");
    console.log("🗑️ Alle Punkte und Rennen zurückgesetzt!");
    updateScoreTable();
}

// 🏆 **Automatisches Aktualisieren der Tabelle**
document.addEventListener("DOMContentLoaded", function () {
    loadStoredTableData(); // 🔄 Lädt gespeicherte Tabelle beim Seitenstart
});

//Beim Laden der Seite
function loadStoredTableData() {
    let storedData = localStorage.getItem("teamScores");

    if (storedData) {
        console.log("📊 Lade gespeicherte Tabelle...");
        let parsedData = JSON.parse(storedData);
        updateScoreTable(parsedData);
    } else {
        console.log("ℹ️ Keine gespeicherten Tabellen-Daten gefunden.");
    }
}

// Bei Veränderung der Punkte
let lastScores = localStorage.getItem("teamScores");

setInterval(() => {
    let currentScores = localStorage.getItem("teamScores");
    if (currentScores !== lastScores) {
        updateScoreTable();
        lastScores = currentScores;
    }
}, 3000);

// Videoaufnahme
async function startCapCard() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const videoElement = document.getElementById("videoFeed");
        videoElement.srcObject = stream;
    } catch (error) {
        console.error("Fehler beim Zugriff auf die Kamera:", error);
    }
}

// Videoaufnahme 
let isOCRRunning = false;
let isPaused = false;
let checkLoopTimeout = null; // Speichert das Intervall

document.getElementById("toggleOCR").addEventListener("click", function () {
    if (!isOCRRunning) {
        isOCRRunning = true;
        console.log("✅ OCR-Prüfung gestartet.");
        startCheckLoop();
        this.textContent = "⏹ STOP"; // Button-Text ändern
    } else {
        isOCRRunning = false;
        console.log("⛔ OCR-Prüfung gestoppt.");
        clearTimeout(checkLoopTimeout); // Loop stoppen
        checkLoopTimeout = null;
        this.textContent = "🔄 START"; // Button-Text zurücksetzen
    }
});

// 🛠 Prüfungsloop (läuft nur, wenn aktiv)
function startCheckLoop() {
    function loop() {
        if (!isOCRRunning || isPaused) return; // 🛑 Stoppt, wenn OCR deaktiviert oder pausiert ist
        captureAndProcessImage(); // Funktion ausführen
        checkLoopTimeout = setTimeout(loop, 1000); // Wiederholen nach 1 Sekunde
    }
    loop();
}

// 📸 Bild erfassen und verarbeiten
    async function captureAndProcessImage() {
    if (isPaused) return; // Falls bereits pausiert, nichts tun
    console.log("📸 Bild wird verarbeitet...");

    let videoElement = document.getElementById("videoFeed");
    let canvas = document.createElement("canvas");
    canvas.width = 1200;
    canvas.height = 675;
    let ctx = canvas.getContext("2d");

    // 📸 Screenshot des gesamten Videos
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    // 🎯 Prüfbereich definieren
    let areaX = 521;
    let areaY = 584;
    let areaWidth = 60;
    let areaHeight = 40;

    // 🎯 Prüfbereich ausschneiden
    let checkCanvas = document.createElement("canvas");
    checkCanvas.width = areaWidth;
    checkCanvas.height = areaHeight;
    let checkCtx = checkCanvas.getContext("2d");
    checkCtx.drawImage(canvas, areaX, areaY, areaWidth, areaHeight, 0, 0, areaWidth, areaHeight);

    // 🔎 Prüfbereich auf dem Browser-Canvas anzeigen
    let previewCanvas = document.getElementById("previewCanvas");
    let previewCtx = previewCanvas.getContext("2d");
    previewCtx.drawImage(checkCanvas, 0, 0, areaWidth, areaHeight);

    // 📌 OpenCV-Bildverarbeitung anwenden
    let processedImageData = sampleProcess(checkCanvas);

    // 🔎 OCR-Prüfung starten
    let isValid = await performCheckOCR(processedImageData);

    if (isValid) {
        console.log("✅ Scoreboard erkannt! Starte OCR...");
        isPaused = true; // 🛑 Prüfloop pausieren
        let fullImageData = canvas.toDataURL("image/png"); 
        performOCR(fullImageData); // ✅ Das geprüfte Bild wird an OCR gesendet

        // ⏸️ 90 Sekunden Pause setzen
        setTimeout(() => {
        isPaused = false;
        if (isOCRRunning) startCheckLoop(); // 🔄 OCR-Loop wieder starten!
        }, 90000);
    } else {
        console.log("❌ Kein Scoreboard erkannt, Bild verworfen.");
    }
}

// 🟢 OCR-Check für den Prüfbereich
async function performCheckOCR(imageData) {
    let detectedText = await sampleText(imageData);
    return detectedText.includes("12");
}

// 🛠 OpenCV-Bildbearbeitung
function sampleProcess(checkCanvas) {
    let src = cv.imread(checkCanvas);
    let dst = new cv.Mat();

    cv.cvtColor(src, dst, cv.COLOR_RGBA2GRAY, 0);
    cv.threshold(dst, dst, 175, 255, cv.THRESH_BINARY);
    cv.morphologyEx(dst, dst, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(1, 1)));
    cv.GaussianBlur(dst, dst, new cv.Size(3, 3), 0, 0, cv.BORDER_DEFAULT);

    // 📌 Ergebnis auf Canvas zurückschreiben
    cv.imshow(checkCanvas, dst);
    src.delete();
    dst.delete();

    return checkCanvas.toDataURL("image/png");
}

// 📖 OCR-Funktion für den Prüfbereich
async function sampleText(imageData) {
    let result = await Tesseract.recognize(
        imageData,
        'eng',
        {
            logger: m => console.log(m),
            tessedit_pageseg_mode: 'PSM_SINGLE_LINE',
            tessedit_char_whitelist: "0123456789"
        }
    );

    let detectedText = result.data.text.trim();
    console.log("OCR-Ergebnis für Prüfung:", detectedText);
    return detectedText;
}
