from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import urllib.error
import urllib.request
import http.client
from datetime import datetime


ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT.parent / "dataset"
LABELS = [
    "0ppm",
    "100ppm",
    "250ppm",
    "500ppm",
    "750ppm",
    "1000ppm",
    "1250ppm",
    "1500ppm",
    "1750ppm",
    "2000ppm",
]


def safe_filename(value):
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip())
    return cleaned.strip("._") or "image"


def fetch_camera_image(camera_url, attempts=3):
    last_error = None
    for _ in range(attempts):
        try:
            request = urllib.request.Request(camera_url, headers={"User-Agent": "dataset-capture/1.0"})
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except (http.client.IncompleteRead, TimeoutError, OSError, urllib.error.URLError) as exc:
            last_error = exc
    raise last_error


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            return self._send_file(ROOT / "index.html", "text/html; charset=utf-8")
        if parsed.path == "/styles.css":
            return self._send_file(ROOT / "styles.css", "text/css; charset=utf-8")
        if parsed.path == "/app.js":
            return self._send_file(ROOT / "app.js", "application/javascript; charset=utf-8")
        if parsed.path == "/labels":
            return self._send_json(200, {"labels": LABELS})
        if parsed.path.startswith("/dataset/"):
            requested = (ROOT.parent / parsed.path.lstrip("/")).resolve()
            if requested.is_file() and requested.is_relative_to(DATASET_DIR.resolve()):
                return self._send_file(requested, "image/jpeg")
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/capture":
            return self._handle_capture()
        if self.path == "/delete":
            return self._handle_delete()
        self._send_json(404, {"error": "Not found"})

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _dataset_file_from_relative_path(self, rel_path):
        requested = (ROOT.parent / rel_path).resolve()
        if not requested.is_relative_to(DATASET_DIR.resolve()):
            return None
        return requested

    def _handle_delete(self):
        data = self._read_json_body()
        rel_path = data.get("path", "").strip().replace("\\", "/")

        if not rel_path.startswith("dataset/"):
            return self._send_json(400, {"error": "Path gambar tidak valid."})

        requested = self._dataset_file_from_relative_path(rel_path)
        if requested is None:
            return self._send_json(400, {"error": "File di luar folder dataset tidak boleh dihapus."})
        if not requested.is_file():
            return self._send_json(404, {"error": "File gambar tidak ditemukan."})

        requested.unlink()
        return self._send_json(200, {"deleted": True, "path": rel_path})

    def _handle_capture(self):
        if self.path != "/capture":
            return self._send_json(404, {"error": "Not found"})

        data = self._read_json_body()
        label = data.get("label", "")
        camera_url = data.get("cameraUrl", "").strip()

        if label not in LABELS:
            return self._send_json(400, {"error": "Label ppm tidak valid."})
        if not camera_url:
            return self._send_json(400, {"error": "URL ESP32-CAM belum diisi."})

        try:
            image, content_type = fetch_camera_image(camera_url)
        except Exception as exc:
            return self._send_json(502, {"error": f"Gagal mengambil gambar dari kamera: {exc}"})

        if not image:
            return self._send_json(502, {"error": "Kamera mengirim gambar kosong."})

        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"

        label_dir = DATASET_DIR / label
        label_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{safe_filename(label)}_{timestamp}{ext}"
        destination = label_dir / filename
        destination.write_bytes(image)

        rel_path = destination.relative_to(ROOT.parent).as_posix()
        self._send_json(200, {"filename": filename, "path": rel_path})


def main():
    DATASET_DIR.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Dataset web siap di http://127.0.0.1:8000")
    print(f"Hasil gambar disimpan ke: {DATASET_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
