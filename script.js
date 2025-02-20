function resizeImage(src, maxWidth) {
    let dst = new cv.Mat();
    let scale = maxWidth / src.cols;
    let newSize = new cv.Size(maxWidth, src.rows * scale);
    cv.resize(src, dst, newSize, 0, 0, cv.INTER_AREA);
    return dst;
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

        img.onload = function () {
            // Originalbild in OpenCV-Mat laden
            let src = cv.imread(img);
            let resized = resizeImage(src, 1200); // Bild auf 1200px Breite skalieren

            // Canvas für das verkleinerte Bild anpassen und zeichnen
            resizedCanvas.width = resized.cols;
            resizedCanvas.height = resized.rows;
            cv.imshow(resizedCanvas, resized);

            let gray = new cv.Mat();
            let blurred = new cv.Mat();
            let thresh = new cv.Mat();
            let morph = new cv.Mat();


            // 1️⃣ Graustufen-Umwandlung
            cv.cvtColor(resized, gray, cv.COLOR_RGBA2GRAY, 0);

            // Schwellenwert für binäres Bild
            cv.threshold(gray, thresh, 165, 255, cv.THRESH_BINARY);

            // Text verbessern
            cv.morphologyEx(thresh, morph, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(1, 1, (1))));

            // 3️⃣ Weichzeichnen (Gaussian Blur)
            cv.GaussianBlur(morph, blurred, new cv.Size(3, 3), 0, 0, cv.BORDER_DEFAULT);

            // 3️⃣ ROI für Spielernamen extrahieren
            let startX = 1013 * (1200 / img.width); // Anpassen an die neue Größe
            let width = 287 * (1200 / img.width);
            let startY = 72 * (1200 / img.width);
            let rowHeight = 78 * (1200 / img.width);
            let numPlayers = 12;

            let placementPoints = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1];
            let teamScores = {};

            // Canvas für die verarbeiteten ROIs vorbereiten
            processedRoiCanvas.width = width;
            processedRoiCanvas.height = numPlayers * rowHeight;

            for (let i = 0; i < numPlayers; i++) {
                let y1 = startY + i * rowHeight;
                let roi = blurred.roi(new cv.Rect(startX, y1, width, rowHeight));

                // ROI-Rahmen auf das verkleinerte Bild zeichnen
                resizedCtx.strokeStyle = "red";
                resizedCtx.lineWidth = 2;
                resizedCtx.strokeRect(startX, y1, width, rowHeight);

                // Verarbeitete ROI auf das zweite Canvas kopieren
                let roiCanvasTemp = document.createElement("canvas");
                roiCanvasTemp.width = width;
                roiCanvasTemp.height = rowHeight;
                let roiCtxTemp = roiCanvasTemp.getContext("2d");
                cv.imshow(roiCanvasTemp, roi);

                processedRoiCtx.drawImage(roiCanvasTemp, 0, i * rowHeight, width, rowHeight);
            

                // OCR auf der verarbeiteten ROI ausführen
                    Tesseract.recognize(
                    roiCanvasTemp.toDataURL(),
                        lang='eng', 
                    { logger: m => console.log(m),
                        tessedit_pageseg_mode: 'PSM_SINGLE_LINE',
                        tessedit_char_whitelist: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                    }
                ).then(({ data: { text } }) => {
                    let cleanName = text.trim();
                    if (cleanName) {
                        let points = placementPoints[i];

                        // Erster Buchstabe als Team-Tag
                        let teamTag = cleanName[0];

                        if (!teamScores[teamTag]) {
                            teamScores[teamTag] = 0;
                        }
                        teamScores[teamTag] += points;

                        // Spieler in HTML-Liste anzeigen
                        let li = document.createElement("li");
                        li.textContent = `${cleanName} → ${points} Punkte`;
                        playerList.appendChild(li);

                        // Name auf resizedCanvas zeichnen
                        resizedCtx.fillStyle = "yellow";
                        resizedCtx.font = "20px Arial";
                        resizedCtx.fillText(cleanName, startX + 5, y1 + rowHeight - 10);
                    }
                });

                roi.delete();
            }

            // Team-Ergebnisse nach kurzer Verzögerung anzeigen
            setTimeout(() => {
                for (let team in teamScores) {
                    let li = document.createElement("li");
                    li.textContent = `Team ${team}: ${teamScores[team]} Punkte`;
                    teamScoresList.appendChild(li);
                }
            }, 1000);

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
