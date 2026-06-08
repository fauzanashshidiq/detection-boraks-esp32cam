import React from "react";
import ReactDOM from "react-dom/client";
import { Camera, History, ImageUp, RefreshCw } from "lucide-react";
import "./styles.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const DEFAULT_CAMERA_URL =
  import.meta.env.VITE_DEFAULT_CAMERA_URL || "http://192.168.1.20/capture";

function App() {
  const [cameraUrl, setCameraUrl] = React.useState(DEFAULT_CAMERA_URL);
  const [result, setResult] = React.useState(null);
  const [history, setHistory] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history`);
      if (!response.ok) throw new Error("Gagal mengambil history");
      setHistory(await response.json());
    } catch (err) {
      setError(err.message);
    }
  }

  async function predictCamera() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/predict/camera`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ camera_url: cameraUrl }),
      });
      if (!response.ok) throw new Error(await readError(response));
      const payload = await response.json();
      setResult(payload);
      await loadHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function predictUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_BASE_URL}/api/predict/upload`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(await readError(response));
      const payload = await response.json();
      setResult(payload);
      await loadHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      event.target.value = "";
    }
  }

  return (
    <main className="app-shell">
      <section className="toolbar">
        <div>
          <h1>Deteksi Boraks</h1>
        </div>
        <button
          className="icon-button"
          onClick={loadHistory}
          aria-label="Refresh history"
        >
          <RefreshCw size={20} />
        </button>
      </section>

      <section className="grid">
        <div className="panel controls">
          <div className="panel-title">
            <Camera size={20} />
            <h2>Kamera</h2>
          </div>
          <label>
            URL capture ESP32-CAM
            <input
              value={cameraUrl}
              onChange={(event) => setCameraUrl(event.target.value)}
            />
          </label>
          <button
            className="primary"
            onClick={predictCamera}
            disabled={loading}
          >
            <Camera size={18} />
            {loading ? "Memproses..." : "Capture & Test"}
          </button>

          <label className="upload-button">
            <ImageUp size={18} />
            Upload Gambar
            <input type="file" accept="image/*" onChange={predictUpload} />
          </label>

          {error && <p className="error">{error}</p>}
        </div>

        <ResultPanel result={result} />
      </section>

      <section className="panel">
        <div className="panel-title">
          <History size={20} />
          <h2>History</h2>
        </div>
        <HistoryTable history={history} />
      </section>
    </main>
  );
}

function ResultPanel({ result }) {
  if (!result) {
    return (
      <div className="panel result-empty">
        <h2>Belum ada hasil</h2>
        <p>Capture dari ESP32-CAM atau upload gambar untuk mulai prediksi.</p>
      </div>
    );
  }

  return (
    <div className="panel result-panel">
      <div className="result-header">
        <span>Kadar terdeteksi</span>
        <strong>{result.label}</strong>
      </div>
      <div className="confidence">
        <span>Confidence</span>
        <strong>{result.confidence_percent}</strong>
      </div>
      <div className="bars">
        {Object.entries(result.probabilities || {}).map(([label, value]) => (
          <div className="bar-row" key={label}>
            <span>{label}</span>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: `${Math.max(value * 100, 2)}%` }}
              />
            </div>
            <b>{(value * 100).toFixed(1)}%</b>
          </div>
        ))}
      </div>
      {result.image_url && (
        <img
          className="preview"
          src={result.image_url}
          alt="Detection result"
        />
      )}
    </div>
  );
}

function HistoryTable({ history }) {
  if (!history.length) {
    return <p className="muted">Belum ada history tersimpan.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Gambar</th>
            <th>Waktu</th>
            <th>Kadar</th>
            <th>Confidence</th>
            <th>Probabilitas</th>
          </tr>
        </thead>
        <tbody>
          {history.map((item) => (
            <tr key={item.id}>
              <td>
                {item.image_url ? (
                  <a href={item.image_url} target="_blank" rel="noreferrer">
                    <img
                      className="history-thumb"
                      src={item.image_url}
                      alt={`Hasil ${item.label}`}
                    />
                  </a>
                ) : (
                  <span className="muted">-</span>
                )}
              </td>
              <td>{formatDate(item.created_at)}</td>
              <td>{item.label}</td>
              <td>{((item.confidence || 0) * 100).toFixed(2)}%</td>
              <td>
                <ProbabilityMiniBars probabilities={item.probabilities} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProbabilityMiniBars({ probabilities }) {
  if (!probabilities || !Object.keys(probabilities).length) {
    return <span className="muted">-</span>;
  }

  return (
    <div className="mini-bars">
      {Object.entries(probabilities).map(([label, value]) => (
        <div className="mini-bar-row" key={label}>
          <span>{label}</span>
          <div className="mini-bar-track">
            <div
              className="mini-bar-fill"
              style={{ width: `${Math.max(value * 100, 2)}%` }}
            />
          </div>
          <b>{(value * 100).toFixed(1)}%</b>
        </div>
      ))}
    </div>
  );
}

async function readError(response) {
  try {
    const payload = await response.json();
    return payload.detail || "Request gagal";
  } catch {
    return "Request gagal";
  }
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
