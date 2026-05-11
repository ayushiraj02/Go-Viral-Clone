const form = document.getElementById("analyzeForm");
const mediaInput = document.getElementById("media");
const preview = document.getElementById("preview");
const results = document.getElementById("results");
const toast = document.getElementById("toast");
const resetBtn = document.getElementById("resetBtn");
const uploadArea = document.getElementById("uploadArea");
const exportBtn = document.getElementById("exportBtn");
const exportFullBtn = document.getElementById("exportFullBtn");
const sampleBtn = document.getElementById("sampleBtn");
const scoreCard = document.querySelector(".score-card");
const resultsSection = document.getElementById("results");
const sampleBadge = document.getElementById("sampleBadge");

const scoreEl = document.getElementById("score");
const summaryEl = document.getElementById("summary");
const hookScore = document.getElementById("hookScore");
const pacingScore = document.getElementById("pacingScore");
const thumbnailScore = document.getElementById("thumbnailScore");
const captionScore = document.getElementById("captionScore");
const trendScore = document.getElementById("trendScore");
const suggestionsEl = document.getElementById("suggestions");
const rewritesEl = document.getElementById("rewrites");
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
const hookReason = document.getElementById("hookReason");
const pacingReason = document.getElementById("pacingReason");
const thumbnailReason = document.getElementById("thumbnailReason");
const captionReason = document.getElementById("captionReason");
const trendReason = document.getElementById("trendReason");
const hookPanel = document.getElementById("hookPanel");

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 2400);
}

const sampleData = {
  platform: "tiktok",
  goal: "engagement",
  caption:
    "This one habit changed my workflow in 7 days. Try it and tell me if it works. #creator #productivity",
  durationSeconds: 19.2,
  hookVisual: 72,
  paceVisual: 68,
  brightness: 64,
  contrast: 58,
};

async function exportScoreCard() {
  if (!scoreCard || typeof html2canvas === "undefined") {
    showToast("Export not available");
    return;
  }

  const canvas = await html2canvas(scoreCard, {
    backgroundColor: "#0f1115",
    scale: 2,
  });
  const link = document.createElement("a");
  link.download = "go-viral-scorecard.png";
  link.href = canvas.toDataURL("image/png");
  link.click();
}

async function exportFullReport() {
  if (!resultsSection || typeof html2canvas === "undefined") {
    showToast("Export not available");
    return;
  }

  const canvas = await html2canvas(resultsSection, {
    backgroundColor: "#0f1115",
    scale: 2,
  });
  const link = document.createElement("a");
  link.download = "go-viral-full-report.png";
  link.href = canvas.toDataURL("image/png");
  link.click();
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

function renderRewrites(items) {
  rewritesEl.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    rewritesEl.appendChild(li);
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

function applySampleData() {
  const captionField = document.getElementById("caption");
  const platformField = document.getElementById("platform");
  const goalField = document.getElementById("goal");

  captionField.value = sampleData.caption;
  platformField.value = sampleData.platform;
  goalField.value = sampleData.goal;
  mediaInput.value = "";
  preview.innerHTML = "";
  if (sampleBadge) {
    sampleBadge.classList.remove("hidden");
  }
}

async function runSampleAnalysis() {
  applySampleData();
  const formData = new FormData(form);
  formData.append("duration_seconds", sampleData.durationSeconds);
  formData.append("hook_visual", sampleData.hookVisual);
  formData.append("pace_visual", sampleData.paceVisual);
  formData.append("brightness", sampleData.brightness);
  formData.append("contrast", sampleData.contrast);

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      showToast(error.detail || "Sample analysis failed");
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

    hookReason.textContent = data.reasons.hook;
    pacingReason.textContent = data.reasons.pacing;
    thumbnailReason.textContent = data.reasons.thumbnail;
    captionReason.textContent = data.reasons.caption;
    trendReason.textContent = data.reasons.trend;
    hookPanel.textContent = data.hook_panel;

    renderSuggestions(data.suggestions);
    renderRewrites(data.rewrites);
    renderChips(trendingAudio, data.trending.audio);
    renderChips(trendingHashtags, data.trending.hashtags);

    yourScoreBar.style.width = `${data.score}%`;
    benchmarkBar.style.width = `${data.comparison.benchmark}%`;
    yourScoreLabel.textContent = data.score;
    benchmarkLabel.textContent = data.comparison.benchmark;
    percentileEl.textContent = `You rank in the top ${data.comparison.percentile}% of similar posts.`;

    showToast("Sample analysis complete");
  } catch (error) {
    showToast("Network error. Is the backend running?");
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

function clamp(value, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

function computeImageStats(imageData) {
  const data = imageData.data;
  let sum = 0;
  let sumSq = 0;
  const pixelCount = data.length / 4;

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    sum += luminance;
    sumSq += luminance * luminance;
  }

  const mean = sum / pixelCount;
  const variance = sumSq / pixelCount - mean * mean;
  const stdDev = Math.sqrt(Math.max(variance, 0));

  return {
    brightness: clamp(Math.round((mean / 255) * 100)),
    contrast: clamp(Math.round((stdDev / 128) * 100)),
  };
}

function getImageMetrics(file) {
  return new Promise((resolve) => {
    if (!file || !file.type.startsWith("image/")) {
      resolve(null);
      return;
    }

    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const scale = Math.min(1, 320 / img.naturalWidth);
      canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
      canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      const stats = computeImageStats(ctx.getImageData(0, 0, canvas.width, canvas.height));
      URL.revokeObjectURL(url);
      resolve({
        width: img.naturalWidth,
        height: img.naturalHeight,
        ...stats,
      });
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
    img.src = url;
  });
}

async function getVideoDuration(file) {
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

async function analyzeVideo(file) {
  if (!file || !file.type.startsWith("video/")) {
    return null;
  }

  const url = URL.createObjectURL(file);
  const video = document.createElement("video");
  video.preload = "metadata";
  video.muted = true;
  video.src = url;

  const ready = await new Promise((resolve) => {
    video.onloadedmetadata = () => resolve(true);
    video.onerror = () => resolve(false);
  });

  if (!ready || !Number.isFinite(video.duration)) {
    URL.revokeObjectURL(url);
    return null;
  }

  const canvas = document.createElement("canvas");
  const targetWidth = 160;
  const scale = targetWidth / video.videoWidth;
  canvas.width = targetWidth;
  canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
  const ctx = canvas.getContext("2d");

  const captureFrame = async (time) => {
    await new Promise((resolve) => {
      video.currentTime = Math.min(time, Math.max(0, video.duration - 0.1));
      const handler = () => {
        video.removeEventListener("seeked", handler);
        resolve();
      };
      video.addEventListener("seeked", handler);
    });
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return ctx.getImageData(0, 0, canvas.width, canvas.height);
  };

  const diffScore = (a, b) => {
    const dataA = a.data;
    const dataB = b.data;
    let diff = 0;
    const pixelCount = dataA.length / 4;
    for (let i = 0; i < dataA.length; i += 4) {
      diff += Math.abs(dataA[i] - dataB[i]);
      diff += Math.abs(dataA[i + 1] - dataB[i + 1]);
      diff += Math.abs(dataA[i + 2] - dataB[i + 2]);
    }
    return diff / (pixelCount * 3);
  };

  const hookTimes = [0.2, 1.2, 2.2, 3.0].filter((t) => t <= video.duration);
  const paceTimes = [0.2, video.duration * 0.25, video.duration * 0.5, video.duration * 0.75].filter(
    (t) => t <= video.duration
  );

  const hookFrames = [];
  for (const time of hookTimes) {
    hookFrames.push(await captureFrame(time));
  }

  const paceFrames = [];
  for (const time of paceTimes) {
    paceFrames.push(await captureFrame(time));
  }

  const computeDiffs = (frames) => {
    if (frames.length < 2) return 0;
    let total = 0;
    for (let i = 1; i < frames.length; i += 1) {
      total += diffScore(frames[i - 1], frames[i]);
    }
    return total / (frames.length - 1);
  };

  const hookDiff = computeDiffs(hookFrames);
  const paceDiff = computeDiffs(paceFrames);
  const stats = computeImageStats(hookFrames[0]);

  URL.revokeObjectURL(url);

  return {
    duration: video.duration,
    hookVisual: clamp(Math.round(hookDiff * 2.2)),
    paceVisual: clamp(Math.round(paceDiff * 2.0)),
    brightness: stats.brightness,
    contrast: stats.contrast,
  };
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
  const [imageMetrics, videoMetrics, duration] = await Promise.all([
    getImageMetrics(file),
    analyzeVideo(file),
    getVideoDuration(file),
  ]);
  if (imageMetrics) {
    formData.append("image_width", imageMetrics.width);
    formData.append("image_height", imageMetrics.height);
    formData.append("brightness", imageMetrics.brightness);
    formData.append("contrast", imageMetrics.contrast);
  }
  if (videoMetrics) {
    formData.append("duration_seconds", videoMetrics.duration);
    formData.append("hook_visual", videoMetrics.hookVisual);
    formData.append("pace_visual", videoMetrics.paceVisual);
    formData.append("brightness", videoMetrics.brightness);
    formData.append("contrast", videoMetrics.contrast);
  } else if (duration) {
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

    hookReason.textContent = data.reasons.hook;
    pacingReason.textContent = data.reasons.pacing;
    thumbnailReason.textContent = data.reasons.thumbnail;
    captionReason.textContent = data.reasons.caption;
    trendReason.textContent = data.reasons.trend;
    hookPanel.textContent = data.hook_panel;

    renderSuggestions(data.suggestions);
    renderRewrites(data.rewrites);
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

if (exportBtn) {
  exportBtn.addEventListener("click", () => {
    if (results.classList.contains("hidden")) {
      showToast("Run an analysis first");
      return;
    }
    exportScoreCard();
  });
}

if (exportFullBtn) {
  exportFullBtn.addEventListener("click", () => {
    if (results.classList.contains("hidden")) {
      showToast("Run an analysis first");
      return;
    }
    exportFullReport();
  });
}

if (sampleBtn) {
  sampleBtn.addEventListener("click", () => {
    runSampleAnalysis();
  });
}

resetBtn.addEventListener("click", () => {
  form.reset();
  preview.innerHTML = "";
  results.classList.add("hidden");
  if (sampleBadge) {
    sampleBadge.classList.add("hidden");
  }
});
