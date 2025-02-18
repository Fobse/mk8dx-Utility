        function performOCR() {
                setTimeout(3000)
            let fileInput = document.getElementById("imageInput");
            let playerList = document.getElementById("playerList");
            let teamScoresList = document.getElementById("teamScores");
            let roiCanvas = document.getElementById("roiCanvas");
            let processedRoiCanvas = document.getElementById("processedRoiCanvas");
            let roiCtx = roiCanvas.getContext("2d");
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
                    // Setze Canvas-Größe auf Bildgröße
                    roiCanvas.width = img.width;
                    roiCanvas.height = img.height;
                    roiCtx.drawImage(img, 0, 0, img.width, img.height);

                    processedRoiCanvas.width = 287; // Breite der ROIs
                    processedRoiCanvas.height = 12 * 78; // Höhe aller 12 ROIs zusammen

                    let src = cv.imread(roiCanvas);
                    let gray = new cv.Mat();
                    let blurred = new cv.Mat();

                    // 1️⃣ Graustufen-Umwandlung
                    cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY, 0);

                    // 2️⃣ Weichzeichnen (Gaussian Blur)
                    cv.GaussianBlur(gray, blurred, new cv.Size(5, 5), 0, 0, cv.BORDER_DEFAULT);

                    // 3️⃣ ROI für Spielernamen extrahieren
                    let startX = 1013, width = 287;
                    let startY = 72, rowHeight = 78;
                    let numPlayers = 12;

                    let placementPoints = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1];
                    let teamScores = {};

                    for (let i = 0; i < numPlayers; i++) {
                        let y1 = startY + i * rowHeight;
                        let y2 = y1 + rowHeight;

                        let roi = blurred.roi(new cv.Rect(startX, y1, width, rowHeight));

                        // Zeichne ROI-Rahmen auf Originalbild (rot)
                        roiCtx.strokeStyle = "red";
                        roiCtx.lineWidth = 2;
                        roiCtx.strokeRect(startX, y1, width, rowHeight);

                        // In separaten Canvas speichern (Graustufen + Blur)
                        processedRoiCtx.drawImage(roiCanvas, startX, y1, width, rowHeight, 0, i * rowHeight, width, rowHeight);

                        // OCR auf bearbeitetem ROI ausführen
                        let roiCanvasTemp = document.createElement("canvas");
                        roiCanvasTemp.width = width;
                        roiCanvasTemp.height = rowHeight;
                        let roiCtxTemp = roiCanvasTemp.getContext("2d");
                        cv.imshow(roiCanvasTemp, roi);

                        Tesseract.recognize(
                            roiCanvasTemp.toDataURL(),
                            'eng',
                            { logger: m => console.log(m) }
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

                                // Name auf Originalbild zeichnen
                                roiCtx.fillStyle = "yellow";
                                roiCtx.font = "20px Arial";
                                roiCtx.fillText(cleanName, startX + 5, y1 + rowHeight - 10);
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
                    }, 3000);

                    src.delete();
                    gray.delete();
                    blurred.delete();
                };
            };

            reader.readAsDataURL(file);
        }
