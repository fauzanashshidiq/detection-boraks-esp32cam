import React from "react";
import ReactDOM from "react-dom/client";
import {
  BarChart3,
  Bell,
  CalendarDays,
  Camera,
  CheckCircle2,
  ChevronRight,
  Download,
  FileText,
  FlaskConical,
  Gauge,
  HelpCircle,
  History,
  ImageUp,
  Maximize2,
  Plus,
  Printer,
  RefreshCw,
  Search,
  Send,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  TestTube2,
  TriangleAlert,
  Wifi,
} from "lucide-react";
import "./styles.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const DEFAULT_CAMERA_URL =
  import.meta.env.VITE_DEFAULT_CAMERA_URL || "http://192.168.1.20/capture";
const FEED_PLACEHOLDER =
  "https://images.unsplash.com/photo-1582719471384-894fbb16e074?auto=format&fit=crop&w=1400&q=80";

const navigation = [
  { id: "test", label: "Pengetesan", icon: FlaskConical },
  { id: "history", label: "Riwayat", icon: History },
  { id: "export", label: "Ekspor Laporan", icon: FileText },
];

function App() {
  const [activePage, setActivePage] = React.useState("test");
  const [cameraUrl, setCameraUrl] = React.useState(DEFAULT_CAMERA_URL);
  const [result, setResult] = React.useState(null);
  const [history, setHistory] = React.useState([]);
  const [query, setQuery] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("all");
  const [selectedIds, setSelectedIds] = React.useState([]);
  const [technician, setTechnician] = React.useState("Dr. Hendrawan Saputra");
  const [notes, setNotes] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    loadHistory();
  }, []);

  React.useEffect(() => {
    setSelectedIds((ids) => ids.filter((id) => history.some((item) => item.id === id)));
  }, [history]);

  const filteredHistory = React.useMemo(
    () => filterHistory(history, query, statusFilter),
    [history, query, statusFilter],
  );
  const selectedRows = React.useMemo(
    () => history.filter((item) => selectedIds.includes(item.id)),
    [history, selectedIds],
  );
  const stats = React.useMemo(() => getStats(history), [history]);

  async function loadHistory() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history`);
      if (!response.ok) throw new Error(await readError(response));
      const payload = await response.json();
      setHistory(payload);
      setError("");
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

  function startNewTest() {
    setActivePage("test");
    setResult(null);
    setError("");
  }

  return (
    <main className="min-h-screen bg-background text-on-surface font-body-md">
      <Sidebar activePage={activePage} setActivePage={setActivePage} onNewTest={startNewTest} />
      <TopBar
        activePage={activePage}
        query={query}
        setQuery={setQuery}
        loading={loading}
        onRefresh={loadHistory}
      />

      <section className="ml-0 min-h-screen pt-[88px] lg:ml-sidebar-width lg:pt-16">
        <div className="px-margin-mobile pb-8 pt-5 lg:px-margin-desktop lg:py-margin-desktop">
          {error && (
            <div className="mb-4 rounded-lg border border-error bg-error-container px-4 py-3 text-on-error-container">
              {error}
            </div>
          )}

          {activePage === "test" && (
            <TestingPage
              cameraUrl={cameraUrl}
              setCameraUrl={setCameraUrl}
              result={result}
              history={history}
              loading={loading}
              onCamera={predictCamera}
              onUpload={predictUpload}
            />
          )}

          {activePage === "history" && (
            <HistoryPage
              history={history}
              filteredHistory={filteredHistory}
              stats={stats}
              query={query}
              setQuery={setQuery}
              statusFilter={statusFilter}
              setStatusFilter={setStatusFilter}
              onExport={() => setActivePage("export")}
            />
          )}

          {activePage === "export" && (
            <ExportPage
              history={history}
              filteredHistory={filteredHistory}
              selectedIds={selectedIds}
              setSelectedIds={setSelectedIds}
              selectedRows={selectedRows}
              stats={stats}
              technician={technician}
              setTechnician={setTechnician}
              notes={notes}
              setNotes={setNotes}
            />
          )}
        </div>
      </section>
    </main>
  );
}

function Sidebar({ activePage, setActivePage, onNewTest }) {
  return (
    <aside className="fixed left-0 top-0 z-50 hidden h-full w-sidebar-width flex-col border-r border-outline-variant bg-tertiary py-8 lg:flex">
      <div className="mb-10 px-6">
        <h1 className="text-headline-md font-bold text-tertiary-fixed">BoraxSense IoT</h1>
        <p className="font-label-md text-label-md text-tertiary-fixed/70">Precision Detection</p>
      </div>

      <nav className="flex-1 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`flex w-full items-center gap-stack-md px-4 py-3 text-left transition-colors ${
                active
                  ? "border-l-4 border-primary bg-primary-container/10 font-bold text-primary-fixed"
                  : "text-tertiary-fixed/70 hover:bg-tertiary-container/50 hover:text-tertiary-fixed"
              }`}
            >
              <Icon size={21} />
              <span className="font-label-md text-label-md">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto space-y-2 px-4">
        <button
          onClick={onNewTest}
          className="mb-8 flex w-full items-center justify-center gap-2 rounded-lg bg-primary-fixed py-3 font-bold text-on-primary-fixed transition-opacity hover:opacity-90"
        >
          <Plus size={18} />
          New Test
        </button>
        <SideLink icon={Settings} label="Settings" />
        <SideLink icon={HelpCircle} label="Support" />
      </div>
    </aside>
  );
}

function SideLink({ icon: Icon, label }) {
  return (
    <button className="flex w-full items-center gap-stack-md rounded px-4 py-2 text-left text-tertiary-fixed/70 transition-colors hover:bg-tertiary-container/50 hover:text-tertiary-fixed">
      <Icon size={20} />
      <span className="font-label-md text-label-md">{label}</span>
    </button>
  );
}

function TopBar({ activePage, query, setQuery, loading, onRefresh }) {
  const title = navigation.find((item) => item.id === activePage)?.label || "System Status";

  return (
    <header className="fixed left-0 right-0 top-0 z-40 flex min-h-16 flex-col gap-3 border-b border-outline-variant bg-surface px-margin-mobile py-3 lg:left-sidebar-width lg:min-h-16 lg:flex-row lg:items-center lg:justify-between lg:px-margin-desktop lg:py-0">
      <div className="flex flex-wrap items-center gap-4 lg:gap-8">
        <h2 className="text-headline-md font-extrabold text-primary">System Status</h2>
        <div className="flex items-center gap-2 rounded-full bg-surface-container px-3 py-1">
          <div className="h-2 w-2 rounded-full bg-[#22c55e] borax-pulse" />
          <span className="font-label-sm text-label-sm text-on-surface-variant">IoT Device Online</span>
        </div>
        <nav className="hidden gap-6 md:flex">
          <span className="border-b-2 border-primary pb-1 font-label-sm text-label-sm font-bold text-primary">
            {title}
          </span>
          <span className="font-label-sm text-label-sm font-medium text-on-surface-variant">Analytics</span>
        </nav>
      </div>

      <div className="flex flex-wrap items-center gap-3 lg:gap-5">
        <label className="relative flex h-10 min-w-[220px] flex-1 items-center rounded-full bg-surface-container-low lg:flex-none">
          <Search className="absolute left-3 text-on-surface-variant" size={17} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Cari data..."
            className="h-full w-full rounded-full border-0 bg-transparent pl-10 pr-4 text-sm outline-none ring-0 focus:ring-2 focus:ring-primary/20"
          />
        </label>
        <button
          onClick={onRefresh}
          className="grid h-10 w-10 place-items-center rounded-lg text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
          aria-label="Refresh data"
        >
          <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
        </button>
        <button className="grid h-10 w-10 place-items-center rounded-lg text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary">
          <Wifi size={20} />
        </button>
        <button className="relative grid h-10 w-10 place-items-center rounded-lg text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary">
          <Bell size={20} />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-error" />
        </button>
        <div className="hidden h-8 w-px bg-outline-variant lg:block" />
        <button className="hidden rounded-lg bg-primary px-4 py-2 font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90 lg:block">
          Sync Device
        </button>
      </div>
    </header>
  );
}

function TestingPage({ cameraUrl, setCameraUrl, result, history, loading, onCamera, onUpload }) {
  const ppm = parsePpm(result?.label);
  const gaugePercent = Math.min((ppm / 2000) * 100, 100);
  const safe = !result || isSafe(result.label);

  return (
    <div className="mx-auto grid max-w-container-max grid-cols-12 gap-gutter">
      <section className="col-span-12 overflow-hidden rounded-xl border border-outline-variant bg-surface-container-lowest shadow-sm lg:col-span-8">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-outline-variant bg-surface-container-low p-4">
          <div className="flex items-center gap-2">
            <Camera className="text-primary" size={20} />
            <span className="font-bold text-on-surface">Kamera ESP32</span>
          </div>
          <div className="flex items-center gap-2 rounded border border-outline-variant bg-surface px-3 py-1 font-label-sm text-label-sm text-on-surface-variant">
            <span>Resolution: 1080p</span>
            <span className="h-1 w-1 rounded-full bg-outline" />
            <span>FPS: 30</span>
          </div>
        </div>

        <div className="relative bg-neutral-900">
          <img
            className="h-[340px] w-full object-cover opacity-90 transition-opacity sm:h-[420px]"
            src={result?.image_url || FEED_PLACEHOLDER}
            alt="Camera capture feed"
          />
          <div className="pointer-events-none absolute inset-0 border-[18px] border-dashed border-primary/10" />
          <div className="absolute bottom-4 right-4 flex gap-2">
            <button className="rounded bg-black/50 p-2 text-white transition-colors hover:bg-black/70" aria-label="Fullscreen">
              <Maximize2 size={20} />
            </button>
            <button className="rounded bg-black/50 p-2 text-white transition-colors hover:bg-black/70" aria-label="Camera settings">
              <SlidersHorizontal size={20} />
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-4 bg-surface p-stack-md xl:flex-row xl:items-center xl:justify-between">
          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
            <input
              value={cameraUrl}
              onChange={(event) => setCameraUrl(event.target.value)}
              className="h-12 rounded-full border border-outline-variant bg-surface-container-lowest px-4 outline-none focus:border-primary"
              aria-label="URL capture ESP32-CAM"
            />
            <button
              onClick={onCamera}
              disabled={loading}
              className="flex h-12 items-center justify-center gap-2 rounded-full bg-primary px-8 font-bold text-on-primary shadow-lg shadow-primary/20 transition-all hover:scale-[1.02] disabled:opacity-70"
            >
              {loading ? <RefreshCw className="animate-spin" size={19} /> : <TestTube2 size={19} />}
              {loading ? "Analysing..." : "Start Test"}
            </button>
            <label className="flex h-12 cursor-pointer items-center justify-center gap-2 rounded-full border border-outline px-6 font-bold text-on-surface-variant transition-colors hover:bg-surface-container">
              <ImageUp size={18} />
              Upload
              <input type="file" accept="image/*" onChange={onUpload} className="hidden" />
            </label>
          </div>
          <div className="text-left xl:text-right">
            <span className="block font-label-sm text-label-sm text-on-surface-variant">Last Calibration</span>
            <span className="font-bold text-on-surface">{formatDate(history[0]?.created_at) || "Belum tersedia"}</span>
          </div>
        </div>
      </section>

      <aside className="col-span-12 flex flex-col gap-gutter lg:col-span-4">
        <ColorMonitor result={result} safe={safe} />
        <ConcentrationGauge result={result} gaugePercent={gaugePercent} safe={safe} />
      </aside>

      <section className="col-span-12 grid grid-cols-1 gap-gutter md:grid-cols-3">
        <StatusCard result={result} safe={safe} />
        <InfoCard icon={Gauge} label="Device Battery" value="84%" />
        <InfoCard icon={BarChart3} label="Confidence" value={result?.confidence_percent || "-"} />
      </section>

      <section className="col-span-12 rounded-xl border border-outline-variant bg-surface-container-lowest p-stack-lg shadow-sm lg:col-span-5">
        <h3 className="mb-6 font-bold text-on-surface">Live Sensor Variance</h3>
        <div className="flex h-48 items-end gap-2 px-2">
          {[40, 55, 45, 70, 30, 15, 42, 58, 48, 20].map((height, index) => (
            <div
              key={index}
              className="flex-1 rounded-t bg-primary/30 transition-all duration-700"
              style={{ height: `${height}%`, opacity: 0.35 + index / 20 }}
            />
          ))}
        </div>
      </section>

      <section className="col-span-12 rounded-xl border border-outline-variant bg-surface-container-lowest p-stack-lg shadow-sm lg:col-span-7">
        <h3 className="mb-6 font-bold text-on-surface">Recent Samples</h3>
        <div className="space-y-4">
          {history.slice(0, 3).map((item, index) => (
            <RecentSample key={item.id || index} item={item} index={index} />
          ))}
          {!history.length && <p className="text-on-surface-variant">Belum ada sampel tersimpan.</p>}
        </div>
      </section>
    </div>
  );
}

function ColorMonitor({ result, safe }) {
  return (
    <section className="rounded-xl border border-outline-variant bg-surface-container-lowest p-stack-lg shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="font-bold text-on-surface">Detection Status</h3>
        <ShieldCheck className="text-outline" size={20} />
      </div>
      <div className="flex flex-col items-center gap-6 py-4">
        <div className="relative flex h-32 w-32 items-center justify-center rounded-full border-4 border-surface-container-high bg-white shadow-inner">
          <div
            className={`h-24 w-24 rounded-full transition-colors duration-500 ${
              safe ? "bg-yellow-400" : "bg-secondary"
            }`}
          />
          <div className="glass-panel absolute -bottom-2 rounded-full border border-outline-variant px-3 py-1 font-label-sm text-label-sm shadow-sm">
            {safe ? "RGB: 255, 215, 0" : "RGB: 144, 77, 0"}
          </div>
        </div>
        <div className="text-center">
          <span className="mb-1 block font-label-sm text-label-sm uppercase text-on-surface-variant">
            Detected Hue
          </span>
          <span className="text-headline-md font-bold text-on-surface">
            {safe ? "Curcumin Yellow" : "Deep Orange"}
          </span>
        </div>
      </div>
    </section>
  );
}

function ConcentrationGauge({ result, gaugePercent, safe }) {
  return (
    <section className="rounded-xl border border-outline-variant bg-surface-container-lowest p-stack-lg shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="font-bold text-on-surface">Borax Concentration</h3>
        <Gauge className="text-primary" size={21} />
      </div>
      <div className="space-y-6">
        <div className="relative h-4 overflow-hidden rounded-full bg-surface-container-high">
          <div
            className={`absolute left-0 top-0 h-full rounded-full transition-all duration-1000 ${
              safe ? "bg-primary" : "bg-secondary"
            }`}
            style={{ width: `${Math.max(gaugePercent, result ? 3 : 0)}%` }}
          />
          <div className="absolute left-[60%] top-0 z-10 h-full w-0.5 bg-error" />
        </div>
        <div className="flex items-end justify-between gap-4">
          <div>
            <span className={`block text-display-lg font-display-lg ${safe ? "text-primary" : "text-secondary"}`}>
              {result?.label || "-"}
            </span>
            <span className="font-label-md text-label-md uppercase text-on-surface-variant">PPM (mg/kg)</span>
          </div>
          <span
            className={`rounded-full border px-3 py-1 font-label-sm text-label-sm ${
              safe
                ? "border-primary/20 bg-primary/10 text-primary"
                : "border-secondary/20 bg-secondary-fixed text-secondary"
            }`}
          >
            {safe ? "Safe Range" : "Detected"}
          </span>
        </div>
        <div className="flex justify-between border-t border-outline-variant pt-4 font-label-sm text-label-sm text-on-surface-variant">
          <span>0ppm</span>
          <span>2000ppm</span>
        </div>
      </div>
    </section>
  );
}

function StatusCard({ result, safe }) {
  const Icon = safe ? CheckCircle2 : TriangleAlert;
  return (
    <div
      className={`flex items-center gap-4 rounded-xl border border-outline-variant bg-surface-container-lowest p-stack-md shadow-sm ${
        safe ? "border-l-4 border-l-primary" : "border-l-4 border-l-secondary"
      }`}
    >
      <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${safe ? "bg-primary/10 text-primary" : "bg-secondary-fixed text-secondary"}`}>
        <Icon size={24} />
      </div>
      <div>
        <span className="block font-label-sm text-label-sm uppercase text-on-surface-variant">Result Analysis</span>
        <span className={`text-headline-md font-bold ${safe ? "text-primary" : "text-secondary"}`}>
          {!result ? "READY" : safe ? "SAFE" : "DETECTED"}
        </span>
      </div>
    </div>
  );
}

function InfoCard({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-outline-variant bg-surface-container-lowest p-stack-md shadow-sm">
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-surface-container text-outline">
        <Icon size={23} />
      </div>
      <div>
        <span className="block font-label-sm text-label-sm uppercase text-on-surface-variant">{label}</span>
        <span className="text-headline-md font-bold text-on-surface">{value}</span>
      </div>
    </div>
  );
}

function RecentSample({ item, index }) {
  const safe = isSafe(item.label);
  return (
    <div className={`flex items-center justify-between gap-3 rounded-lg border p-3 ${safe ? "border-outline-variant/50 bg-surface" : "border-error/20 bg-error/5"}`}>
      <div className="flex min-w-0 items-center gap-4">
        <div className={`h-3 w-3 shrink-0 rounded-full ${safe ? "bg-primary" : "bg-error"}`} />
        <span className="truncate font-label-md text-label-md">Sample_#{item.id?.slice(0, 4) || index + 1}</span>
      </div>
      <span className="font-label-sm text-label-sm text-on-surface-variant">{item.label}</span>
      <span className={`font-bold ${safe ? "text-primary" : "text-error"}`}>{safe ? "PASSED" : "DETECTED"}</span>
    </div>
  );
}

function HistoryPage({
  history,
  filteredHistory,
  stats,
  query,
  setQuery,
  statusFilter,
  setStatusFilter,
  onExport,
}) {
  return (
    <div className="mx-auto max-w-container-max">
      <div className="mb-stack-lg flex flex-col gap-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-headline-lg font-headline-lg text-on-surface">Riwayat Pengetesan</h1>
            <p className="mt-1 text-on-surface-variant">Kelola dan tinjau data hasil laboratorium IoT secara real-time.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <FilterButton icon={CalendarDays} label="Rentang Waktu" />
            <FilterButton icon={SlidersHorizontal} label="Filter Status" />
            <button
              onClick={onExport}
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90"
            >
              <Download size={18} />
              Ekspor
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <StatTile icon={TestTube2} label="Total Sampel" value={stats.total} />
          <StatTile icon={CheckCircle2} label="Lolos Uji" value={stats.safe} tone="safe" />
          <StatTile icon={TriangleAlert} label="Terdeteksi Borax" value={stats.detected} tone="alert" />
          <StatTile icon={Gauge} label="Rata-rata Akurasi" value={stats.averageConfidence} />
        </div>
      </div>

      <HistoryFilters
        query={query}
        setQuery={setQuery}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
      />
      <HistoryTable history={filteredHistory} total={history.length} />

      <div className="mt-stack-lg grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="relative overflow-hidden rounded-xl border border-outline-variant bg-white p-8 xl:col-span-2">
          <div className="relative z-10 max-w-xl">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <span className="rounded bg-primary/10 px-3 py-1 text-xs font-bold uppercase tracking-widest text-primary">
                Quick Insight
              </span>
              <span className="text-sm text-on-surface-variant">Last 24 Hours Analysis</span>
            </div>
            <h3 className="mb-2 text-headline-md font-headline-md">Borax Concentration Trends</h3>
            <p className="text-on-surface-variant">
              Ringkasan otomatis mengikuti riwayat deteksi terbaru dari backend dan siap diekspor sebagai laporan.
            </p>
          </div>
          <div className="mt-8 flex flex-wrap gap-4">
            <button onClick={onExport} className="flex items-center gap-2 rounded-lg bg-primary px-6 py-3 font-bold text-white transition-opacity hover:opacity-90">
              <Download size={18} />
              Export Report
            </button>
            <button className="flex items-center gap-2 rounded-lg border border-primary px-6 py-3 font-bold text-primary transition-colors hover:bg-primary/5">
              <BarChart3 size={18} />
              View Analytics
            </button>
          </div>
        </section>
        <section className="flex min-h-[260px] flex-col items-center justify-center rounded-xl bg-tertiary p-8 text-center text-white">
          <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-white/10 borax-pulse">
            <Wifi className="text-primary-fixed" size={36} />
          </div>
          <h4 className="mb-2 text-headline-md font-headline-md">Sensor Healthy</h4>
          <p className="mb-6 text-sm text-tertiary-fixed/80">Device ID: BS-IOT-4929</p>
          <div className="flex items-center gap-2 font-bold text-primary-fixed">
            <div className="h-3 w-3 rounded-full bg-[#4ade80]" />
            LIVE MONITORING
          </div>
        </section>
      </div>
    </div>
  );
}

function FilterButton({ icon: Icon, label }) {
  return (
    <button className="flex items-center gap-2 rounded-lg border border-outline px-4 py-2 text-on-surface-variant transition-colors hover:bg-surface-container">
      <Icon size={18} />
      {label}
    </button>
  );
}

function StatTile({ icon: Icon, label, value, tone = "default" }) {
  const styles = {
    default: "bg-primary-container/20 text-primary",
    safe: "bg-[#dcfce7] text-[#166534]",
    alert: "bg-error-container text-error",
  };
  return (
    <div className={`flex items-center gap-4 rounded-xl border border-outline-variant bg-surface p-6 ${tone === "alert" ? "border-t-4 border-t-secondary" : ""}`}>
      <div className={`flex h-12 w-12 items-center justify-center rounded-full ${styles[tone]}`}>
        <Icon size={23} />
      </div>
      <div>
        <p className="font-label-sm text-label-sm uppercase text-on-surface-variant">{label}</p>
        <p className={`text-headline-md font-headline-md ${tone === "alert" ? "text-secondary" : ""}`}>{value}</p>
      </div>
    </div>
  );
}

function HistoryFilters({ query, setQuery, statusFilter, setStatusFilter }) {
  return (
    <section className="mb-4 flex flex-col gap-3 rounded-xl border border-outline-variant bg-surface p-4 md:flex-row">
      <label className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" size={18} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="h-11 w-full rounded-full border border-outline-variant bg-surface-container-low pl-10 pr-4 outline-none focus:border-primary"
          placeholder="Search history..."
        />
      </label>
      <select
        value={statusFilter}
        onChange={(event) => setStatusFilter(event.target.value)}
        className="h-11 rounded-lg border border-outline-variant bg-surface-container-low px-3 outline-none focus:border-primary"
      >
        <option value="all">Semua Status</option>
        <option value="safe">Lolos</option>
        <option value="detected">Tidak Lolos</option>
      </select>
    </section>
  );
}

function HistoryTable({ history, total }) {
  return (
    <section className="overflow-hidden rounded-xl border border-outline-variant bg-surface">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] border-collapse text-left">
          <thead>
            <tr className="border-b border-outline-variant bg-surface-container-low">
              <TableHead>Date/Time</TableHead>
              <TableHead>Sample Name</TableHead>
              <TableHead>Color Intensity</TableHead>
              <TableHead>Borax Level (PPM)</TableHead>
              <TableHead>Status</TableHead>
              <TableHead align="text-right">Actions</TableHead>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {history.map((item, index) => (
              <HistoryRow key={item.id || index} item={item} index={index} />
            ))}
            {!history.length && (
              <tr>
                <td className="px-6 py-8 text-center text-on-surface-variant" colSpan="6">
                  Belum ada data riwayat.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex flex-col gap-3 border-t border-outline-variant bg-surface px-6 py-4 md:flex-row md:items-center md:justify-between">
        <span className="text-sm text-on-surface-variant">Showing {history.length ? 1 : 0} to {history.length} of {total} entries</span>
        <div className="flex gap-2">
          <PaginationButton disabled label="Previous" />
          <button className="h-10 w-10 rounded bg-primary font-medium text-on-primary">1</button>
          <PaginationButton label="2" />
          <PaginationButton label="3" />
        </div>
      </div>
    </section>
  );
}

function TableHead({ children, align = "" }) {
  return (
    <th className={`px-6 py-4 font-label-md text-label-md uppercase tracking-wider text-on-surface-variant ${align}`}>
      {children}
    </th>
  );
}

function HistoryRow({ item, index }) {
  const safe = isSafe(item.label);
  return (
    <tr className={`transition-colors hover:bg-surface-container-lowest ${safe ? "" : "bg-secondary/5"}`}>
      <td className="px-6 py-4">
        <div className="flex flex-col">
          <span className="font-medium text-on-surface">{formatDateOnly(item.created_at)}</span>
          <span className="text-sm text-on-surface-variant">{formatTimeOnly(item.created_at)}</span>
        </div>
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-surface-variant">
            <TestTube2 size={18} />
          </div>
          <span className="font-medium">Sample #{item.id?.slice(0, 6) || index + 1}</span>
        </div>
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center gap-2">
          <div className={`h-4 w-4 rounded-full shadow-sm ${safe ? "bg-primary-fixed" : "bg-secondary"}`} />
          <span className="font-label-sm text-label-sm">{safe ? "Low (Curcumin Yellow)" : "High (Deep Orange)"}</span>
        </div>
      </td>
      <td className="px-6 py-4">
        <span className={`font-label-md text-label-md font-bold ${safe ? "text-on-surface-variant" : "text-secondary"}`}>
          {item.label}
        </span>
      </td>
      <td className="px-6 py-4">
        <StatusBadge label={item.label} />
      </td>
      <td className="px-6 py-4 text-right">
        <a
          href={item.image_url || "#"}
          target={item.image_url ? "_blank" : undefined}
          rel="noreferrer"
          className="ml-auto inline-flex items-center justify-end gap-1 text-sm font-medium text-primary hover:underline"
        >
          View Details
          <ChevronRight size={18} />
        </a>
      </td>
    </tr>
  );
}

function PaginationButton({ label, disabled = false }) {
  return (
    <button
      disabled={disabled}
      className="h-10 min-w-10 rounded border border-outline px-3 font-medium transition-colors hover:bg-surface-container disabled:opacity-50"
    >
      {label}
    </button>
  );
}

function ExportPage({
  history,
  filteredHistory,
  selectedIds,
  setSelectedIds,
  selectedRows,
  stats,
  technician,
  setTechnician,
  notes,
  setNotes,
}) {
  const rowsForReport = selectedRows.length ? selectedRows : filteredHistory.slice(0, 5);

  function toggleSelected(id) {
    setSelectedIds((ids) => (ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id]));
  }

  function selectAll() {
    setSelectedIds(filteredHistory.map((item) => item.id).filter(Boolean));
  }

  function clearSelection() {
    setSelectedIds([]);
  }

  return (
    <div className="mx-auto max-w-container-max">
      <section className="mb-stack-lg">
        <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h3 className="text-headline-lg font-headline-lg text-on-surface">Summary Dashboard</h3>
            <p className="text-on-surface-variant">Ringkasan aktivitas pengetesan 30 hari terakhir.</p>
          </div>
          <div className="flex w-fit items-center gap-2 rounded border border-primary/20 bg-primary-container/10 px-3 py-1 font-label-md text-label-md text-primary">
            <CalendarDays size={16} />
            30 Hari Terakhir
          </div>
        </div>
        <div className="grid grid-cols-1 gap-gutter md:grid-cols-2 xl:grid-cols-4">
          <ReportStat icon={TestTube2} label="Total Pengetesan" value={stats.total} delta="+12%" />
          <ReportStat icon={TriangleAlert} label="Borax Terdeteksi" value={stats.detected} delta="+2" tone="alert" />
          <ReportStat icon={Wifi} label="Waktu Aktif Sensor" value="99.8%" delta="Online" />
          <ReportStat icon={FileText} label="Laporan Diekspor" value={Math.max(1, Math.ceil(history.length / 3))} />
        </div>
      </section>

      <div className="grid grid-cols-1 gap-gutter xl:grid-cols-12">
        <div className="space-y-gutter xl:col-span-7">
          <section className="overflow-hidden rounded-xl border border-outline-variant bg-surface">
            <div className="flex flex-col gap-3 border-b border-outline-variant bg-surface-container-low p-6 md:flex-row md:items-center md:justify-between">
              <h4 className="text-headline-md font-headline-md">Pilih Hasil Pengetesan</h4>
              <div className="flex gap-2">
                <button onClick={selectAll} className="rounded px-3 py-1 font-label-md text-label-md text-primary hover:bg-primary/10">
                  Pilih Semua
                </button>
                <button onClick={clearSelection} className="rounded px-3 py-1 font-label-md text-label-md text-on-surface-variant hover:bg-surface-variant">
                  Hapus Pilihan
                </button>
              </div>
            </div>
            <div className="custom-scrollbar max-h-[400px] overflow-y-auto">
              <table className="w-full min-w-[680px] border-collapse text-left">
                <thead className="sticky top-0 z-10 bg-surface-container-high">
                  <tr>
                    <th className="border-b border-outline-variant p-4 font-label-sm text-label-sm">Pilih</th>
                    <th className="border-b border-outline-variant p-4 font-label-sm text-label-sm">ID Tes</th>
                    <th className="border-b border-outline-variant p-4 font-label-sm text-label-sm">Tanggal</th>
                    <th className="border-b border-outline-variant p-4 font-label-sm text-label-sm">Sampel</th>
                    <th className="border-b border-outline-variant p-4 text-right font-label-sm text-label-sm">Hasil</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.map((item, index) => (
                    <SelectableRow
                      key={item.id || index}
                      item={item}
                      index={index}
                      selected={selectedIds.includes(item.id)}
                      onToggle={() => toggleSelected(item.id)}
                    />
                  ))}
                  {!filteredHistory.length && (
                    <tr>
                      <td className="p-6 text-center text-on-surface-variant" colSpan="5">
                        Belum ada hasil pengetesan.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-xl border border-outline-variant bg-surface p-6">
            <h4 className="mb-6 text-headline-md font-headline-md">Konfigurasi Laporan</h4>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="space-y-3">
                <label className="block font-label-md text-label-md text-on-surface">Format Dokumen</label>
                <div className="grid grid-cols-3 gap-2">
                  <FormatButton icon={FileText} label="PDF" active />
                  <FormatButton icon={FileText} label="CSV" />
                  <FormatButton icon={BarChart3} label="Excel" />
                </div>
              </div>
              <label className="space-y-3">
                <span className="block font-label-md text-label-md text-on-surface">Nama Teknisi</span>
                <input
                  value={technician}
                  onChange={(event) => setTechnician(event.target.value)}
                  className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest p-3 outline-none focus:border-primary"
                />
              </label>
            </div>
            <label className="mt-6 block">
              <span className="mb-2 block font-label-md text-label-md text-on-surface">Catatan Tambahan</span>
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest p-3 outline-none focus:border-primary"
                rows="3"
                placeholder="Tambahkan observasi khusus atau ringkasan metodologi laboratorium..."
              />
            </label>
            <div className="mt-6 flex gap-4 rounded-lg border border-tertiary/10 bg-tertiary/5 p-4">
              <div className="h-fit rounded bg-tertiary p-2 text-white">
                <Send size={18} />
              </div>
              <div>
                <p className="font-label-md text-label-md text-on-surface">Tanda Tangan Digital</p>
                <p className="mb-3 text-xs text-on-surface-variant">Tanda tangan yang tersimpan akan disematkan otomatis.</p>
                <button className="rounded border border-tertiary bg-surface px-4 py-1.5 font-label-sm text-label-sm text-tertiary transition-colors hover:bg-tertiary hover:text-white">
                  Atur Tanda Tangan
                </button>
              </div>
            </div>
          </section>
        </div>

        <ReportPreview
          rows={rowsForReport}
          technician={technician}
          notes={notes}
          onDownload={() => downloadCsv(rowsForReport)}
        />
      </div>
    </div>
  );
}

function ReportStat({ icon: Icon, label, value, delta, tone = "default" }) {
  const alert = tone === "alert";
  return (
    <div className={`relative overflow-hidden rounded-xl border bg-surface p-stack-md ${alert ? "border-error/30" : "border-outline-variant"}`}>
      {alert && <div className="absolute left-0 top-0 h-1 w-full bg-error" />}
      <div className="mb-4 flex items-start justify-between">
        <div className={`rounded-lg p-2 ${alert ? "bg-error-container text-error" : "bg-primary-container/20 text-primary"}`}>
          <Icon size={22} />
        </div>
        {delta && <span className={`font-label-sm text-label-sm ${alert ? "text-error" : "text-primary"}`}>{delta}</span>}
      </div>
      <div className={`text-display-lg font-display-lg ${alert ? "text-error" : "text-primary"}`}>{value}</div>
      <div className="font-label-md text-label-md text-on-surface-variant">{label}</div>
    </div>
  );
}

function SelectableRow({ item, index, selected, onToggle }) {
  const safe = isSafe(item.label);
  return (
    <tr className={`cursor-pointer transition-colors hover:bg-surface-container ${safe ? "" : "bg-error-container/5"}`} onClick={onToggle}>
      <td className="border-b border-outline-variant p-4">
        <input
          checked={selected}
          onChange={onToggle}
          onClick={(event) => event.stopPropagation()}
          className="h-4 w-4 rounded border-outline-variant text-primary focus:ring-primary"
          type="checkbox"
        />
      </td>
      <td className="border-b border-outline-variant p-4 font-label-md text-label-md">#BRX-{String(index + 1).padStart(4, "0")}</td>
      <td className="border-b border-outline-variant p-4 text-sm text-on-surface-variant">{formatDate(item.created_at)}</td>
      <td className="border-b border-outline-variant p-4 text-sm">Sample #{item.id?.slice(0, 6) || index + 1}</td>
      <td className="border-b border-outline-variant p-4 text-right">
        <StatusBadge label={item.label} compact />
      </td>
    </tr>
  );
}

function FormatButton({ icon: Icon, label, active = false }) {
  return (
    <button
      className={`flex flex-col items-center justify-center rounded-xl p-3 transition-all ${
        active
          ? "border-2 border-primary bg-primary/5 text-primary"
          : "border border-outline-variant text-on-surface-variant hover:border-primary/50"
      }`}
    >
      <Icon className="mb-1" size={21} />
      <span className="font-label-sm text-label-sm">{label}</span>
    </button>
  );
}

function ReportPreview({ rows, technician, notes, onDownload }) {
  return (
    <aside className="xl:col-span-5">
      <div className="sticky top-24 overflow-hidden rounded-xl border border-outline-variant bg-surface shadow-lg">
        <div className="flex items-center justify-between border-b border-outline-variant bg-surface-container-highest p-4">
          <div className="flex items-center gap-2">
            <FileText className="text-on-surface-variant" size={19} />
            <span className="font-label-md text-label-md">Preview Laporan</span>
          </div>
          <span className="text-xs italic text-on-surface-variant">Halaman 1 dari 1</span>
        </div>

        <div className="relative aspect-[1/1.41] overflow-hidden bg-white p-8">
          <div className="mb-6 flex items-start justify-between border-b-2 border-primary pb-4">
            <div>
              <h5 className="text-xl font-bold uppercase tracking-wider text-primary">Laboratorium Analisis Pangan</h5>
              <p className="text-[10px] text-on-surface-variant">Laporan Resmi Deteksi Boraks IoT - BoraxSense</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] font-bold">NOMOR LAPORAN</p>
              <p className="font-mono text-[12px]">LAB/BRX/{new Date().getFullYear()}/0042</p>
            </div>
          </div>

          <div className="mb-8 grid grid-cols-2 gap-4">
            <div>
              <p className="text-[9px] font-bold text-on-surface-variant">DICETAK OLEH</p>
              <p className="text-[11px]">{technician || "-"}</p>
            </div>
            <div>
              <p className="text-[9px] font-bold text-on-surface-variant">TANGGAL PENERBITAN</p>
              <p className="text-[11px]">{formatDateOnly(new Date().toISOString())}</p>
            </div>
          </div>

          <div className="border border-outline-variant">
            <table className="w-full text-[10px]">
              <thead className="bg-surface-container">
                <tr>
                  <th className="border-b border-r border-outline-variant p-2 text-left">ID SAMPEL</th>
                  <th className="border-b border-r border-outline-variant p-2 text-left">SAMPLING</th>
                  <th className="border-b border-outline-variant p-2 text-right">HASIL AKHIR</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 5).map((row, index) => (
                  <tr key={row.id || index} className={isSafe(row.label) ? "" : "bg-error-container/10"}>
                    <td className="border-b border-r border-outline-variant p-2">#BRX-{String(index + 1).padStart(4, "0")}</td>
                    <td className="border-b border-r border-outline-variant p-2">Sample #{row.id?.slice(0, 6) || index + 1}</td>
                    <td className={`border-b border-outline-variant p-2 text-right font-bold ${isSafe(row.label) ? "text-primary" : "text-error"}`}>
                      {isSafe(row.label) ? "NEGATIF" : `POSITIF (${row.label})`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-8">
            <p className="mb-2 text-[9px] font-bold text-on-surface-variant">CATATAN LABORATORIUM:</p>
            <p className="border-l-2 border-outline-variant pl-3 text-[10px] italic leading-relaxed text-on-surface-variant">
              {notes || "Analisis dilakukan menggunakan sensor BoraxSense dengan integrasi model klasifikasi berbasis citra."}
            </p>
          </div>

          <div className="absolute bottom-12 right-12 w-32 text-center">
            <p className="mb-8 text-[9px]">Disahkan Oleh,</p>
            <div className="flex h-12 items-center justify-center overflow-hidden border-b border-on-surface">
              <span className="font-label-md text-label-md italic text-primary">Verified</span>
            </div>
            <p className="mt-1 text-[10px] font-bold">{technician?.split(" ").slice(-1)[0] || "Analyst"}</p>
            <p className="text-[8px] uppercase text-on-surface-variant">Senior Analyst</p>
          </div>

          <div className="absolute bottom-4 left-8 right-8 flex justify-between border-t border-outline-variant pt-2">
            <span className="text-[8px] text-on-surface-variant">BoraxSense IoT - Laboratory Cloud Connectivity Enabled</span>
            <span className="text-[8px] text-on-surface-variant">UUID: local-report</span>
          </div>
        </div>

        <div className="flex flex-col gap-3 bg-surface-container p-6">
          <button
            onClick={onDownload}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3 font-bold text-white shadow-md transition-opacity hover:opacity-90"
          >
            <Download size={19} />
            Generate & Unduh Laporan
          </button>
          <div className="flex gap-3">
            <button className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-outline py-2 font-label-md text-label-md text-on-surface transition-colors hover:bg-white">
              <Printer size={17} />
              Cetak
            </button>
            <button className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-outline py-2 font-label-md text-label-md text-on-surface transition-colors hover:bg-white">
              <Send size={17} />
              Email
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}

function StatusBadge({ label, compact = false }) {
  const safe = isSafe(label);
  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${
        compact ? "px-2.5 py-0.5 text-xs" : "px-3 py-1 text-sm"
      } ${
        safe
          ? "border-primary/20 bg-primary-container/10 text-primary"
          : "border-secondary/20 bg-orange-100 text-secondary"
      }`}
    >
      {safe ? "Lolos" : "Tidak Lolos"}
    </span>
  );
}

function filterHistory(history, query, statusFilter) {
  const needle = query.trim().toLowerCase();
  return history.filter((item) => {
    const statusMatches =
      statusFilter === "all" ||
      (statusFilter === "safe" && isSafe(item.label)) ||
      (statusFilter === "detected" && !isSafe(item.label));
    const textMatches =
      !needle ||
      [item.label, item.source, item.created_at, item.id].some((value) =>
        String(value || "").toLowerCase().includes(needle),
      );
    return statusMatches && textMatches;
  });
}

function getStats(history) {
  const safe = history.filter((item) => isSafe(item.label)).length;
  const confidenceValues = history.map((item) => Number(item.confidence || 0)).filter(Boolean);
  const average =
    confidenceValues.length > 0
      ? confidenceValues.reduce((total, value) => total + value, 0) / confidenceValues.length
      : 0;

  return {
    total: history.length,
    safe,
    detected: history.length - safe,
    averageConfidence: confidenceValues.length ? `${(average * 100).toFixed(1)}%` : "-",
  };
}

function isSafe(label) {
  return parsePpm(label) === 0;
}

function parsePpm(label) {
  const parsed = Number.parseInt(String(label || "").replace(/[^\d]/g, ""), 10);
  return Number.isFinite(parsed) ? parsed : 0;
}

function downloadCsv(rows) {
  const headers = ["id", "created_at", "label", "status", "confidence", "source", "image_url"];
  const csvRows = [
    headers.join(","),
    ...rows.map((row) =>
      headers
        .map((header) => {
          const value =
            header === "status" ? (isSafe(row.label) ? "Lolos" : "Tidak Lolos") : row[header] ?? "";
          return `"${String(value).replaceAll('"', '""')}"`;
        })
        .join(","),
    ),
  ];

  const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `borax-report-${new Date().toISOString().slice(0, 10)}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
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

function formatDateOnly(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "medium",
  }).format(new Date(value));
}

function formatTimeOnly(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("id-ID", {
    timeStyle: "medium",
  }).format(new Date(value));
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
