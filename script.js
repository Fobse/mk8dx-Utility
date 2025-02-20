function resizeImage(src, maxWidth) {
    let dst = new cv.Mat();
    let scale = maxWidth / src.cols;
    let newSize = new cv.Size(src.cols * scale, src.rows * scale);
    cv.resize(src, dst, newSize, 0, 0, cv.INTER_AREA);
    return dst;
}

// 🏆 NEU: Team-Logik-Funktionen direkt darunter einfügen
function detectTeamSize(players) {
    let playerCount = players.length;
    let possibleSizes = [2, 3, 4];

    for (let size of possibleSizes) {
        if (playerCount % size === 0) {
            return size;
        }
    }
    return null; // Fehler: Keine gültige Teamgröße gefunden
}

function analyzeTeams(players) {
    let teamCounts = {};
    let unassignedPlayers = [];

    console.log("🔍 ANALYZE TEAMS - Eingelesene Spieler:", players);

    for (let player of players) {
        let tag = player.teamTag;
        console.log(`📌 Spieler: ${player.name}, Erkannter Team-Tag: "${tag}"`);

        if (tag && Object.keys(teamCounts).includes(tag)) {
            teamCounts[tag]++;
            console.log(`✅ Spieler ${player.name} zum Team ${tag} hinzugefügt.`);
        } else if (tag) {
            unassignedPlayers.push(player);
            console.warn(`⚠ Spieler ${player.name} hat einen unbekannten Tag ("${tag}") und wurde als unassigned gespeichert.`);
        } else {
            unassignedPlayers.push(player);
            console.warn(`⚠ Spieler ${player.name} hat GAR KEINEN Tag und wurde als unassigned gespeichert.`);
        }
    }

    console.log("📌 Endgültige Team-Verteilung:", teamCounts);
    console.log("📌 Unassigned Spieler:", unassignedPlayers);

    return { teamCounts, unassignedPlayers };
}

function assignUnassignedPlayers(unassignedPlayers, teamCounts, teamSize) {
    console.log("🔄 ZUWEISUNG DER UNASSIGNED SPIELER startet...");
    console.log("📌 Aktuelle Teams vor der Zuweisung:", teamCounts);
    console.log("📌 Unassigned Spieler vor der Zuweisung:", unassignedPlayers);

    for (let player of unassignedPlayers) {
        let bestMatch = Object.entries(teamCounts).find(([team, count]) => count < teamSize);

        if (bestMatch) {
            let teamTag = bestMatch[0];
            player.teamTag = teamTag;
            teamCounts[teamTag]++;

            console.log(`✅ Spieler ${player.name} wurde zu Team ${teamTag} hinzugefügt.`);
        } else {
            console.warn(`🚨 Konnte Spieler ${player.name} KEINEM Team zuweisen!`);
        }
    }

    console.log("📌 Finale Team-Verteilung nach der Zuweisung:", teamCounts);
}

function performOCR() {
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
            cv.threshold(gray, thresh, 140, 255, cv.THRESH_BINARY);
            cv.morphologyEx(thresh, morph, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(1, 1)));
            cv.GaussianBlur(morph, blurred, new cv.Size(3, 3), 0, 0, cv.BORDER_DEFAULT);

            let scale = 1200 / img.width;
            let startX = 1013 * scale;
            let width = 287 * scale;
            let startY = 72 * scale;
            let rowHeight = 78 * scale;
            let numPlayers = 12;
            let placementPoints = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1];
            let players = [];

            processedRoiCanvas.width = width;
            processedRoiCanvas.height = numPlayers * rowHeight;

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
                        let teamTag = cleanName[0];
                        players.push({ name: cleanName, teamTag, points: placementPoints[i] });

                        let li = document.createElement("li");
                        li.textContent = `${cleanName} → ${placementPoints[i]} Punkte`;
                        playerList.appendChild(li);

                        resizedCtx.fillStyle = "yellow";
                        resizedCtx.font = "20px Arial";
                        resizedCtx.fillText(cleanName, startX + 5, y1 + rowHeight - 10);
                    }
                });

                ocrPromises.push(ocrPromise);
                roi.delete();
            }

            await Promise.all(ocrPromises); // 🏆 OCR wartet auf alle Spieler

            let teamSize = detectTeamSize(players);
            if (!teamSize) {
                alert("Fehler: Ungültige Spieleranzahl!");
                return;
            }

            let { teamCounts, unassignedPlayers } = analyzeTeams(players);
            assignUnassignedPlayers(unassignedPlayers, teamCounts, teamSize);

            let teamScores = {};
            for (let player of players) {
                if (!teamScores[player.teamTag]) {
                    teamScores[player.teamTag] = 0;
                }
                teamScores[player.teamTag] += player.points;
            }

            for (let team in teamScores) {
                let li = document.createElement("li");
                li.textContent = `Team ${team}: ${teamScores[team]} Punkte`;
                teamScoresList.appendChild(li);
            }

            console.log("Finale Teams:", teamCounts);

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
