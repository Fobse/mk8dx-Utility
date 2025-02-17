        function performOCR() {
            let fileInput = document.getElementById("imageInput");
            let playerList = document.getElementById("playerList");
            let teamScoresList = document.getElementById("teamScores");
            let canvas = document.getElementById("outputCanvas");
            let ctx = canvas.getContext("2d");

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
                    canvas.width = img.width;
                    canvas.height = img.height;
                    ctx.drawImage(img, 0, 0, img.width, img.height);

                    let src = cv.imread(canvas);
                    let gray = new cv.Mat();
                    let blurred = new cv.Mat();

                    // 1️⃣ Graustufen-Umwandlung
                    cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY, 0);

                    // 2️⃣ Weichzeichnen (Gaussian Blur)
                    cv.GaussianBlur(gray, blurred, new cv.Size(3, 3), 0, 0, cv.BORDER_DEFAULT);

                    // 3️⃣ ROI für Spielernamen extrahieren (x, y, Breite, Höhe)
                    let startX = 1013, width = 287;
                    let startY = 72, rowHeight = 78;
                    let numPlayers = 12;

                    let placementPoints = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1];
                    let teamScores = {};

                    for (let i = 0; i < numPlayers; i++) {
                        let y1 = startY + i * rowHeight;
                        let y2 = y1 + rowHeight;

                        let roi = blurred.roi(new cv.Rect(startX, y1, width, rowHeight));

                        // In Canvas speichern für OCR
                        let roiCanvas = document.createElement("canvas");
                        roiCanvas.width = width;
                        roiCanvas.height = rowHeight;
                        let roiCtx = roiCanvas.getContext("2d");
                        cv.imshow(roiCanvas, roi);

                        // 4️⃣ Texterkennung mit Tesseract.js
                        Tesseract.recognize(
                            roiCanvas.toDataURL(),
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
                            }
                        });

                        roi.delete();
                    }

                    // Team-Ergebnisse ausgeben
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
    </script>
</body>
</html>
