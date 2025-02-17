function performOCR() {
    let fileInput = document.getElementById("imageInput");
    let output = document.getElementById("output");

    if (fileInput.files.length === 0) {
        output.innerText = "Bitte ein Bild hochladen!";
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
                'eng', // Sprache (du kannst 'deu' für Deutsch nutzen)
                {
                    logger: m => console.log(m) // Fortschritt in der Konsole sehen
                }
            ).then(({ data: { text } }) => {
                output.innerText = text; // Zeigt den erkannten Text an
            }).catch(err => {
                output.innerText = "Fehler bei der Erkennung!";
                console.error(err);
            });
        };
    };

    reader.readAsDataURL(file);
}
