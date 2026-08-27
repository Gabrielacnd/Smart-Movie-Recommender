const API_URL = window.location.origin || "http://127.0.0.1:8000";
let recognition = null;
let recognizing = false;
let lastRecommendation = { title: "", summary: "" };

async function sendQuery() {
    const query = document.getElementById("query").value.trim();
    const recommendButton = document.getElementById("recommendButton");
    const loadingMessage = document.getElementById("loadingMessage");
    const warningMessage = document.getElementById("warningMessage");
    const resultCard = document.getElementById("result");
    const imageButton = document.getElementById("generateImageButton");
    const img = document.getElementById("bookImage");
    const imageLoadingMessage = document.getElementById("imageLoadingMessage");

    if (!query) {
        alert("Te rog introdu un text pentru recomandare.");
        return;
    }

    warningMessage?.classList.add("hidden");
    if (warningMessage) warningMessage.innerText = "";

    recommendButton.disabled = true;
recommendButton.innerText = "Se caută...";

    loadingMessage?.classList.remove("hidden");
    if (loadingMessage) {
        loadingMessage.innerText = "Așteaptă, pregătesc recomandarea...";
    }

    resultCard?.classList.add("hidden");

    img?.classList.add("hidden");
    img?.removeAttribute("src");
    imageLoadingMessage?.classList.add("hidden");
    imageButton?.classList.add("hidden");
    imageButton?.setAttribute("disabled", "true");

    try {
        const response = await fetch(`${API_URL}/api/recommend`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query })
        });

        const data = await response.json();
        console.log("RECOMMEND RESPONSE:", data);

        if (!response.ok) {
            alert(data.detail || "A apărut o eroare.");
            return;
        }

        if (data.flagged) {
            if (warningMessage) {
                warningMessage.innerText = data.message;
                warningMessage.classList.remove("hidden");
            }
            resultCard?.classList.add("hidden");
            return;
        }

        document.getElementById("title").innerText = data.title || "";
        document.getElementById("recommendation").innerText = data.recommendation || "";
        document.getElementById("summary").innerText = data.summary || "";

        lastRecommendation = {
            title: data.title || "",
            summary: data.summary || ""
        };

        resultCard?.classList.remove("hidden");

        if (data.image_url) {
            const fullImageUrl = data.image_url.startsWith("http")
                ? `${data.image_url}?t=${Date.now()}`
                : `${API_URL}${data.image_url}?t=${Date.now()}`;
            img.src = fullImageUrl;
            img.classList.remove("hidden");
            imageLoadingMessage?.classList.add("hidden");
        } else {
            img?.classList.add("hidden");
            img?.removeAttribute("src");
            imageLoadingMessage?.classList.add("hidden");
        }

        if (imageButton) {
            imageButton.disabled = false;
            imageButton.classList.remove("hidden");
            imageButton.innerText = "🎨 Generează poster";
        }
    } catch (error) {
        console.error("EROARE ÎN sendQuery:", error);
        alert("A apărut o eroare. Deschide F12 > Console.");
    } finally {
        recommendButton.disabled = false;
        recommendButton.innerText = "Recomandă un film";
        loadingMessage?.classList.add("hidden");
    }
}

async function generateImageFromLastResult() {
    if (!lastRecommendation.title) {
        return;
    }
    await generateImage(lastRecommendation.title, lastRecommendation.summary);
}

async function generateImage(title, summary) {
    console.log("A INTRAT IN generateImage()");
    const img = document.getElementById("bookImage");
    const imageLoadingMessage = document.getElementById("imageLoadingMessage");
    const imageButton = document.getElementById("generateImageButton");

    if (imageButton) {
        imageButton.disabled = true;
        imageButton.innerText = "Se generează posterul...";
    }

    try {
        const response = await fetch(`${API_URL}/api/generate-image`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ title, summary })
        });

        const data = await response.json();
        console.log("IMAGE RESPONSE:", data);

        if (!response.ok) {
            console.error("Image API error:", data.detail);
            imageLoadingMessage?.classList.add("hidden");
            img?.classList.add("hidden");
            return;
        }

        if (!data.image_url) {
            console.warn("Nu s-a primit image_url.");
            imageLoadingMessage?.classList.add("hidden");
            img?.classList.add("hidden");
            if (imageButton) {
                imageButton.disabled = false;
                imageButton.innerText = "🎨 Generează poster";
            }
            return;
        }

        const fullImageUrl = data.image_url.startsWith("http")
            ? `${data.image_url}?t=${Date.now()}`
            : `${API_URL}${data.image_url}?t=${Date.now()}`;
        console.log("IMAGE URL:", fullImageUrl);

        img.onload = () => {
            console.log("Imagine încărcată OK");
            img.classList.remove("hidden");
            imageLoadingMessage?.classList.add("hidden");
            if (imageButton) {
                imageButton.disabled = false;
                imageButton.innerText = "🎨 Generează poster";
            }
        };

        img.onerror = () => {
            console.error("Imaginea nu s-a putut încărca:", fullImageUrl);
            img.classList.add("hidden");
            imageLoadingMessage?.classList.add("hidden");
            if (imageButton) {
                imageButton.disabled = false;
                imageButton.innerText = "🎨 Generează poster";
            }
        };

        img.src = fullImageUrl;
    } catch (error) {
        console.error("Eroare la generateImage:", error);
        img?.classList.add("hidden");
        imageLoadingMessage?.classList.add("hidden");
        if (imageButton) {
            imageButton.disabled = false;
            imageButton.innerText = "🎨 Generează poster";
        }
    }
}

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn("Browserul nu suportă recunoașterea vocală.");
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "ro-RO";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
        recognizing = true;
        const voiceButton = document.getElementById("voiceButton");
        const status = document.getElementById("voiceStatus");

        voiceButton.classList.add("recording");
        voiceButton.innerText = "⏺";
        status.classList.remove("hidden");
        status.innerText = "Vorbește acum...";
    };

    recognition.onend = () => {
        recognizing = false;
        const voiceButton = document.getElementById("voiceButton");
        const status = document.getElementById("voiceStatus");

        voiceButton.classList.remove("recording");
        voiceButton.innerText = "🎤";
        status.classList.remove("hidden");
        status.innerText = "Transcriere finalizată.";
    };

    recognition.onerror = (event) => {
        recognizing = false;
        const voiceButton = document.getElementById("voiceButton");
        const status = document.getElementById("voiceStatus");

        voiceButton.classList.remove("recording");
        voiceButton.innerText = "🎤";
        status.classList.remove("hidden");
        status.innerText = "Eroare de recunoaștere: " + (event.error || "necunoscută");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById("query").value = transcript;
    };
}

function toggleVoiceRecognition() {
    if (!recognition) {
        initSpeechRecognition();
        if (!recognition) {
            alert("Browserul tău nu suportă recunoașterea vocală. Folosește Chrome sau Edge.");
            return;
        }
    }

    if (recognizing) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initSpeechRecognition();
});