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
        alert("Bitte erst eine Teamgröße wählen!");
        return;
    }

    teamTags = {};
    let numTeams = 12 / selectedTeamSize;

    for (let i = 0; i < numTeams; i++) {
        let tag = document.getElementById(`teamTag_${i}`).value.trim();
        if (tag) {
            teamTags[i] = tag;
        } else {
            alert("Bitte alle Team-Tags ausfüllen!");
            return;
        }
    }

    console.log("📌 Gespeicherte Team-Tags:", teamTags);
    alert("Team-Tags wurden übernommen!");
}


async function performOCR() {
    let fileInput = document.getElementById("imageInput");
    let playerList = document.getElementById("playerList");
    let teamScoresList = document.getElementById("teamScores");
    let resizedCanvas = document.getElementById("resizedCanvas");
    let processedRoiCanvas = document.getElementById("processedRoiCanvas");
    let resizedCtx = resizedCanvas.getContext("2d");
    let processedRoiCtx = processedRoiCanvas.getContext("2d");

    playerList.innerHTML = "";
    teamScoresList.innerHTML = "";

    if (fileInput.files.length === 0) {
        alert("Bitte ein Bild hochladen!");
        return;
    }

    console.log("🚀 OCR-Analyse gestartet...");

    let file = fileInput.files[0];
    let reader = new FileReader();

    reader.onload = function () {
        let img = new Image();
        img.src = reader.result;

        img.onload = async function () {
            let src = cv.imread(img);
            let resized = resizeImage(src, 1200);

            resizedCanvas.width = resized.cols;
            resizedCanvas.height = resized.rows;
            cv.imshow(resizedCanvas, resized);

            let gray = new cv.Mat();
            let blurred = new cv.Mat();
            let thresh = new cv.Mat();
            let morph = new cv.Mat();

            cv.cvtColor(resized, gray, cv.COLOR_RGBA2GRAY, 0);
            cv.threshold(gray, thresh, 175, 255, cv.THRESH_BINARY);
            cv.morphologyEx(thresh, morph, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(1, 1)));
            cv.GaussianBlur(morph, blurred, new cv.Size(3, 3), 0, 0, cv.BORDER_DEFAULT);

            let scale = 1200 / img.width;
            let startX = 1013 * scale;
            let width = 287 * scale;
            let startY = 72 * scale;
            let rowHeight = 78 * scale;
            let numPlayers = 12;
            let placementPoints = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1];

            processedRoiCanvas.width = width;
            processedRoiCanvas.height = numPlayers * rowHeight;

            console.log("🔎 Team-Tags gespeichert:", teamTags);

            // OCR separat ausführen
            let players = await recognizePlayers(blurred, startX, startY, width, rowHeight, numPlayers, placementPoints, resizedCtx, processedRoiCtx);
            
            // Wenn OCR erfolgreich war → Punkte berechnen
            if (players.length > 0) {
                calculateTeamScores(players, teamScoresList);
            } else {
                console.warn("⚠️ Keine Spieler erkannt!");
            }

            // Speicher freigeben
            src.delete();
            resized.delete();
            gray.delete();
            blurred.delete();
            thresh.delete();
            morph.delete();
        };
    };

    reader.readAsDataURL(file);
}

// 🎯 **1️⃣ Separater OCR-Prozess**
async function recognizePlayers(blurred, startX, startY, width, rowHeight, numPlayers, placementPoints, resizedCtx, processedRoiCtx) {
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

                // 🏆 Richtige Team-Zuordnung
                let teamIndex = Math.floor(i / selectedTeamSize);
                let teamTag = teamTags[teamIndex];

                console.log(`🎯 Spieler erkannt: ${cleanName} → ${points} Punkte → Team: ${teamTag}`);

                players.push({ name: cleanName, teamTag, points });
            } else {
                console.warn(`⚠️ Spieler an Position ${i + 1} wurde nicht erkannt!`);
            }
        });

        ocrPromises.push(ocrPromise);
        roi.delete();
    }

    await Promise.all(ocrPromises);
    return players;
}

// 🏆 **2️⃣ Punkte nach der OCR berechnen**
function calculateTeamScores(players, teamScoresList) {
    let teamScores = {}; // Team-Punkte zurücksetzen

    for (let player of players) {
        if (!teamScores[player.teamTag]) {
            teamScores[player.teamTag] = 0;
        }
        teamScores[player.teamTag] += player.points;
    }

    console.log("🏆 Finale Team-Ergebnisse:", teamScores);

    // 📌 Ergebnisse in HTML ausgeben
    teamScoresList.innerHTML = ""; // Vorherige Ergebnisse löschen
    for (let team in teamScores) {
        let li = document.createElement("li");
        li.textContent = `Team ${team}: ${teamScores[team]} Punkte`;
        teamScoresList.appendChild(li);
    }
}
