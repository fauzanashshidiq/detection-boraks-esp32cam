const labelGrid = document.querySelector("#labelGrid");
const cameraUrlInput = document.querySelector("#cameraUrl");
const captureBtn = document.querySelector("#captureBtn");
const statusEl = document.querySelector("#status");
const preview = document.querySelector("#preview");
const previewBox = document.querySelector(".preview-box");
const historyList = document.querySelector("#historyList");
const captureCount = document.querySelector("#captureCount");
const activeLabelEl = document.querySelector("#activeLabel");

let labels = [];
let selectedLabel = "0ppm";
let count = 0;
let currentPreviewPath = "";

function setStatus(message, type = "normal") {
  statusEl.textContent = message;
  statusEl.style.color = type === "error" ? "#a02d2d" : "#53645a";
}

function renderLabels() {
  labelGrid.innerHTML = "";
  labels.forEach((label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `label-option${label === selectedLabel ? " active" : ""}`;
    button.textContent = label;
    button.addEventListener("click", () => {
      selectedLabel = label;
      activeLabelEl.textContent = label;
      renderLabels();
    });
    labelGrid.appendChild(button);
  });
}

async function loadLabels() {
  const response = await fetch("/labels");
  const data = await response.json();
  labels = data.labels;
  selectedLabel = labels[0];
  activeLabelEl.textContent = selectedLabel;
  renderLabels();
}

async function captureImage() {
  captureBtn.disabled = true;
  setStatus("Mengambil gambar dari ESP32-CAM...");

  try {
    const response = await fetch("/capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        label: selectedLabel,
        cameraUrl: cameraUrlInput.value,
      }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Gagal menyimpan gambar.");
    }

    const cacheBust = Date.now();
    previewBox.classList.remove("has-image");
    preview.removeAttribute("src");
    preview.src = `/${data.path.replaceAll("\\", "/")}?t=${cacheBust}`;
    await preview.decode();
    previewBox.classList.add("has-image");
    currentPreviewPath = data.path;

    historyList.prepend(createHistoryItem(data));

    count += 1;
    captureCount.textContent = count;
    setStatus(`Tersimpan: ${data.path}`);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    captureBtn.disabled = false;
  }
}

function createHistoryItem(data) {
  const item = document.createElement("li");

  const meta = document.createElement("div");
  meta.className = "history-meta";

  const filename = document.createElement("strong");
  filename.textContent = data.filename;

  const path = document.createElement("span");
  path.textContent = data.path;

  meta.append(filename, path);

  const deleteBtn = document.createElement("button");
  deleteBtn.type = "button";
  deleteBtn.className = "delete-btn";
  deleteBtn.textContent = "Hapus";
  deleteBtn.addEventListener("click", () => deleteImage(data.path, item));

  item.append(meta, deleteBtn);
  return item;
}

async function deleteImage(path, item) {
  setStatus("Menghapus gambar...");

  try {
    const response = await fetch("/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Gagal menghapus gambar.");
    }

    item.remove();
    count = Math.max(0, count - 1);
    captureCount.textContent = count;

    if (currentPreviewPath === path) {
      currentPreviewPath = "";
      preview.removeAttribute("src");
      previewBox.classList.remove("has-image");
    }

    setStatus(`Dihapus: ${path}`);
  } catch (error) {
    setStatus(error.message, "error");
  }
}

captureBtn.addEventListener("click", captureImage);
loadLabels().catch((error) => setStatus(error.message, "error"));
