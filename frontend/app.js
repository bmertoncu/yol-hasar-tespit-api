// DOM Elementleri
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const img = document.getElementById('img');
const canvas = document.getElementById('canvas');
const container = document.getElementById('container');
const sendBtn = document.getElementById('sendBtn');
const ctx = canvas.getContext('2d');

// Sabitler
const CONFIDENCE_THRESHOLD = 0.71;
const API_BASE_URL = ' https://ready-houses-sneeze.loca.lt'; // Kendi güncel tünel adresini buraya yaz
const ADANA_BOUNDS = {
    minLat: 36.0, maxLat: 38.5,
    minLon: 34.0, maxLon: 37.0
};

// Oturum ve Konum
let sessionId = localStorage.getItem('sessionId') || Math.random().toString(36).substring(2, 15);
localStorage.setItem('sessionId', sessionId);
let lastLocation = "Location_Unknown";

/**
 * Konum Fonksiyonu
 */
async function getUserLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve("Geolocation_Not_Supported");
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => resolve(`${pos.coords.latitude},${pos.coords.longitude}`),
            async () => {
                try {
                    const response = await fetch('https://ipapi.co/json/');
                    const data = await response.json();
                    resolve(data.latitude && data.longitude ? `${data.latitude},${data.longitude}` : "Location_Fetch_Failed");
                } catch (e) { resolve("IP_API_Failed"); }
            },
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
    });
}

// Görsel Yükleme ve Adana Sınır Kontrolü
dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 1. Konum Al ve Sınır Kontrolü Yap
    lastLocation = await getUserLocation();
    if (lastLocation !== "Location_Fetch_Failed" && lastLocation !== "IP_API_Failed") {
        const [lat, lon] = lastLocation.split(',').map(Number);
        if (lat < ADANA_BOUNDS.minLat || lat > ADANA_BOUNDS.maxLat || 
            lon < ADANA_BOUNDS.minLon || lon > ADANA_BOUNDS.maxLon) {
            console.log("Tespit edilen konum:", lat, lon);
            alert("Fotoğrafınız Adana dışında tespit edildi. Lütfen Adana sınırları içindeyken bir fotoğraf yükleyin.");
            
            location.reload();
            return;
        }
    }

    // 2. Görseli İşle
    img.src = URL.createObjectURL(file);
    container.style.display = 'block';
    await new Promise(resolve => img.onload = resolve);
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            body: formData,
            headers: { 'X-Session-ID': sessionId }
        });

        const data = await response.json();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const validDetections = data.detections?.filter(d => d.confidence >= CONFIDENCE_THRESHOLD) || [];

        if (validDetections.length > 0) {
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 4;
            const scaleX = canvas.width / img.naturalWidth;
            const scaleY = canvas.height / img.naturalHeight;
            validDetections.forEach(det => {
                const [x1, y1, x2, y2] = Array.isArray(det.bbox[0]) ? det.bbox[0] : det.bbox;
                ctx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);
            });
            sendBtn.style.display = 'block';
        } else {
            alert("Çukur tespit edilemedi.");
            location.reload();
        }
    } catch (err) { alert("Analiz başarısız oldu."); }
});

// Rapor Gönderme
sendBtn.addEventListener('click', async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, location: lastLocation })
        });
        if (response.ok) {
            alert("Rapor başarıyla iletildi!");
            location.reload();
        }
    } catch (err) { alert("Bağlantı hatası."); }
});