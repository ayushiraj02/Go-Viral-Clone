const form = document.getElementById("analyzeForm");
const mediaInput = document.getElementById("media");
const preview = document.getElementById("preview");
const results = document.getElementById("results");
const toast = document.getElementById("toast");
const resetBtn = document.getElementById("resetBtn");
const uploadArea = document.getElementById("uploadArea");

const scoreEl = document.getElementById("score");
const summaryEl = document.getElementById("summary");
const hookScore = document.getElementById("hookScore");
const pacingScore = document.getElementById("pacingScore");
const thumbnailScore = document.getElementById("thumbnailScore");
const captionScore = document.getElementById("captionScore");
const trendScore = document.getElementById("trendScore");
const suggestionsEl = document.getElementById("suggestions");
const trendingAudio = document.getElementById("trendingAudio");
const trendingHashtags = document.getElementById("trendingHashtags");
const hookBar = document.getElementById("hookBar");
const pacingBar = document.getElementById("pacingBar");
const thumbnailBar = document.getElementById("thumbnailBar");
const captionBar = document.getElementById("captionBar");
const trendBar = document.getElementById("trendBar");
const yourScoreBar = document.getElementById("yourScoreBar");
const benchmarkBar = document.getElementById("benchmarkBar");
const yourScoreLabel = document.getElementById("yourScoreLabel");
const benchmarkLabel = document.getElementById("benchmarkLabel");
const percentileEl = document.getElementById("percentile");

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 2400);
}

function setBar(bar, value) {
  bar.style.width = `${value}%`;
}

function renderChips(container, items) {
  container.innerHTML = "";
  items.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = item;
    container.appendChild(chip);
  });
}

function renderSuggestions(items) {
  suggestionsEl.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    suggestionsEl.appendChild(li);
  });
}

function renderPreview(file) {
  preview.innerHTML = "";
  if (!file) return;

  const url = URL.createObjectURL(file);
  if (file.type.startsWith("image/")) {
    const img = document.createElement("img");
    img.src = url;
    preview.appendChild(img);
  } else if (file.type.startsWith("video/")) {
    const video = document.createElement("video");
    video.src = url;
    video.controls = true;
    preview.appendChild(video);
  }
}

function getImageDimensions(file) {
  return new Promise((resolve) => {
    if (!file || !file.type.startsWith("image/")) {
      resolve(null);
      return;
    }

    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
    img.src = url;
  });
}

function getVideoDuration(file) {
  return new Promise((resolve) => {
    if (!file || !file.type.startsWith("video/")) {
      resolve(null);
      return;
    }

    const video = document.createElement("video");
    const url = URL.createObjectURL(file);
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      if (Number.isFinite(video.duration)) {
        resolve(video.duration);
      } else {
        resolve(null);
      }
    };
    video.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
    video.src = url;
  });
}

mediaInput.addEventListener("change", (event) => {
  const file = event.target.files[0];
  renderPreview(file);
});

uploadArea.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadArea.classList.add("dragover");
});

uploadArea.addEventListener("dragleave", () => {
  uploadArea.classList.remove("dragover");
});

uploadArea.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadArea.classList.remove("dragover");
  const file = event.dataTransfer.files[0];
  if (file) {
    mediaInput.files = event.dataTransfer.files;
    renderPreview(file);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const file = mediaInput.files[0];
  const [dims, duration] = await Promise.all([
    getImageDimensions(file),
    getVideoDuration(file),
  ]);
  if (dims) {
    formData.append("image_width", dims.width);
    formData.append("image_height", dims.height);
  }
  if (duration) {
    formData.append("duration_seconds", duration);
  }

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      showToast(error.detail || "Analysis failed");
      return;
    }

    const data = await response.json();
    results.classList.remove("hidden");

    scoreEl.textContent = data.score;
    summaryEl.textContent = data.summary;

    hookScore.textContent = data.breakdown.hook;
    pacingScore.textContent = data.breakdown.pacing;
    thumbnailScore.textContent = data.breakdown.thumbnail;
    captionScore.textContent = data.breakdown.caption;
    trendScore.textContent = data.breakdown.trend;

    setBar(hookBar, data.breakdown.hook);
    setBar(pacingBar, data.breakdown.pacing);
    setBar(thumbnailBar, data.breakdown.thumbnail);
    setBar(captionBar, data.breakdown.caption);
    setBar(trendBar, data.breakdown.trend);

    renderSuggestions(data.suggestions);
    renderChips(trendingAudio, data.trending.audio);
    renderChips(trendingHashtags, data.trending.hashtags);

    yourScoreBar.style.width = `${data.score}%`;
    benchmarkBar.style.width = `${data.comparison.benchmark}%`;
    yourScoreLabel.textContent = data.score;
    benchmarkLabel.textContent = data.comparison.benchmark;
    percentileEl.textContent = `You rank in the top ${data.comparison.percentile}% of similar posts.`;

    showToast("Analysis complete");
  } catch (error) {
    showToast("Network error. Is the backend running?");
  }
});

resetBtn.addEventListener("click", () => {
  form.reset();
  preview.innerHTML = "";
  results.classList.add("hidden");
});
