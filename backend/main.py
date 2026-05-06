from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI(title="Go Viral Analyzer", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

HOOK_WORDS = [
    "wait",
    "watch",
    "here is",
    "here's",
    "you need",
    "stop",
    "secret",
    "mistake",
    "before",
    "after",
]

TRENDING_AUDIO = {
    "tiktok": ["Neon Drift", "Slow Burn", "Midnight Bounce"],
    "instagram": ["Glasswave", "Sunset Drive", "Velvet Echo"],
    "youtube": ["Voltage Loop", "Brightline", "On Repeat"],
}

TRENDING_TAGS = {
    "tiktok": ["#fyp", "#viral", "#learnontiktok", "#creator"],
    "instagram": ["#reels", "#explore", "#creatorlife", "#trending"],
    "youtube": ["#shorts", "#creator", "#howto", "#viral"],
}

PLATFORM_LABELS = {
    "tiktok": "TikTok",
    "instagram": "Instagram Reels",
    "youtube": "YouTube Shorts",
}


class Breakdown(BaseModel):
    hook: int
    pacing: int
    thumbnail: int
    caption: int
    trend: int


class Comparison(BaseModel):
    benchmark: int
    delta: int
    percentile: int


class Trending(BaseModel):
    audio: List[str]
    hashtags: List[str]


class AnalysisResponse(BaseModel):
    score: int
    summary: str
    breakdown: Breakdown
    suggestions: List[str]
    comparison: Comparison
    trending: Trending


def clamp(value: float, min_value: int = 0, max_value: int = 100) -> int:
    return int(max(min_value, min(int(round(value)), max_value)))


def hash_seed(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def caption_metrics(caption: str) -> tuple[int, int]:
    clean = caption.strip()
    length = len(clean)
    hashtags = clean.count("#")
    return length, hashtags


def score_caption(length: int, hashtags: int, intent_score: int) -> int:
    length_score = 100 - abs(length - 120) * 0.6
    hash_score = 100 - abs(hashtags - 3) * 12
    return clamp((length_score * 0.55) + (hash_score * 0.25) + (intent_score * 0.2))


def score_hook(caption: str, file_size_mb: Optional[float]) -> int:
    text = caption.lower()
    hit = any(word in text for word in HOOK_WORDS)
    hook_base = 72 if hit else 52
    size_penalty = 0
    if file_size_mb is not None:
        size_penalty = max(0, (file_size_mb - 8) * 2)
    return clamp(hook_base - size_penalty)


def score_pacing(
    file_size_mb: Optional[float],
    duration_seconds: Optional[float],
    platform: str,
) -> int:
    if duration_seconds is None:
        if file_size_mb is None:
            return 55
        target = 7 if platform == "tiktok" else 9
        diff = abs(file_size_mb - target)
        return clamp(90 - diff * 6)

    target_seconds = 18 if platform == "tiktok" else 24
    diff = abs(duration_seconds - target_seconds)
    return clamp(92 - diff * 2.2)


def score_thumbnail(image_size: Optional[tuple[int, int]], platform: str) -> int:
    if image_size is None:
        return 58

    width, height = image_size
    if height == 0:
        return 58

    ratio = width / height
    target_ratio = 9 / 16 if platform in {"tiktok", "instagram"} else 9 / 16
    ratio_score = 100 - abs(ratio - target_ratio) * 220
    pixel_score = 100 - max(0, 720 - min(width, height)) * 0.05
    return clamp((ratio_score * 0.6) + (pixel_score * 0.4))


def score_trend(hashtags: int, caption: str, platform: str) -> int:
    tags = TRENDING_TAGS.get(platform, [])
    matches = sum(tag.lower() in caption.lower() for tag in tags)
    return clamp(50 + (hashtags * 6) + (matches * 10))


def detect_language(caption: str) -> str:
    for char in caption:
        if "\u0900" <= char <= "\u097f":
            return "hi"
    return "en"


def hook_examples(platform: str, language: str) -> List[str]:
    platform_examples = {
        "tiktok": [
            "Start with a result in the first second: 'This saved me 3 hours.'",
            "Lead with a bold claim: 'Most creators do this wrong.'",
        ],
        "instagram": [
            "Open with a contrast: 'Before vs after in 5 seconds.'",
            "Use a quick promise: 'Watch this to fix your reel.'",
        ],
        "youtube": [
            "Tease the payoff: 'The last tip is the real game-changer.'",
            "Use a challenge: 'Can you spot the mistake in 3 seconds?'",
        ],
    }
    examples = platform_examples.get(
        platform, platform_examples["tiktok"]).copy()
    if language != "en":
        examples.append(
            "Consider a bilingual hook: local language + English keyword.")
    return examples[:2]


def detect_intent(caption: str) -> int:
    text = caption.lower()
    score = 50
    if "?" in text or any(word in text for word in ["how", "why", "what", "tips"]):
        score += 15
    if any(word in text for word in ["follow", "subscribe", "comment", "share", "save"]):
        score += 15
    if any(token in text for token in ["1.", "2.", "3.", "- ", "• "]):
        score += 10
    return clamp(score)


def build_suggestions(
    breakdown: Breakdown,
    caption_length: int,
    hashtags: int,
    platform: str,
    language: str,
    intent_score: int,
) -> List[str]:
    suggestions: List[str] = []
    platform_label = PLATFORM_LABELS.get(platform, platform.title())

    if breakdown.hook < 65:
        suggestions.append(
            "Open with a sharper first line like a bold claim or a surprise result.")
        suggestions.extend(hook_examples(platform, language))
    if breakdown.pacing < 65:
        suggestions.append(
            "Tighten pacing with quicker cuts in the first 5 seconds.")
    if breakdown.thumbnail < 65:
        suggestions.append(
            "Use a high-contrast thumbnail with one focal subject.")
    if breakdown.caption < 70:
        if caption_length < 80:
            suggestions.append(
                "Expand the caption to 80 to 150 characters for clarity.")
        else:
            suggestions.append(
                "Trim the caption to remove filler words and keep it punchy.")
    if hashtags < 2:
        suggestions.append(
            "Add 2 to 4 niche hashtags plus one broad platform hashtag.")
    if breakdown.trend < 60:
        suggestions.append(
            f"Use 1 trending audio track popular on {platform_label}.")
    if intent_score < 70:
        suggestions.append(
            "Add a clear CTA like 'Follow for part 2' or a question to prompt comments.")
    if language != "en":
        suggestions.append(
            "Detected a non-English caption. Test bilingual captions to widen reach.")

    if not suggestions:
        suggestions.append(
            "Strong fundamentals. Test two caption variations to push engagement.")

    return suggestions


def analysis_summary(score: int) -> str:
    if score >= 85:
        return "High viral potential. Only minor edits needed to maximize reach."
    if score >= 70:
        return "Solid foundations with a few quick wins to boost performance."
    if score >= 55:
        return "Average potential. Focus on hook and pacing to lift retention."
    return "Low potential today. Strengthen the hook and simplify the message."


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    caption: str = Form(""),
    platform: str = Form("tiktok"),
    goal: str = Form("reach"),
    image_width: Optional[int] = Form(None),
    image_height: Optional[int] = Form(None),
    duration_seconds: Optional[float] = Form(None),
    media: Optional[UploadFile] = File(None),
) -> AnalysisResponse:
    media_bytes: Optional[bytes] = None
    image_size: Optional[tuple[int, int]] = None
    file_size_mb: Optional[float] = None

    if media is not None:
        media_bytes = await media.read()
        file_size_mb = len(media_bytes) / (1024 * 1024)

    if image_width and image_height:
        image_size = (image_width, image_height)

    caption_length, hashtags = caption_metrics(caption)
    language = detect_language(caption)
    intent_score = detect_intent(caption)

    breakdown = Breakdown(
        hook=score_hook(caption, file_size_mb),
        pacing=score_pacing(file_size_mb, duration_seconds, platform),
        thumbnail=score_thumbnail(image_size, platform),
        caption=score_caption(caption_length, hashtags, intent_score),
        trend=score_trend(hashtags, caption, platform),
    )

    weights = {
        "hook": 0.3,
        "pacing": 0.2,
        "thumbnail": 0.2,
        "caption": 0.2,
        "trend": 0.1,
    }
    weighted_score = (
        breakdown.hook * weights["hook"]
        + breakdown.pacing * weights["pacing"]
        + breakdown.thumbnail * weights["thumbnail"]
        + breakdown.caption * weights["caption"]
        + breakdown.trend * weights["trend"]
    )

    goal_bonus = 2 if goal == "engagement" else 0
    score = clamp(weighted_score + goal_bonus)

    seed_input = f"{caption}-{media.filename if media else ''}-{file_size_mb}-{platform}"
    rng = random.Random(hash_seed(seed_input))
    benchmark = clamp(rng.randint(60, 82))
    delta = score - benchmark
    percentile = clamp(50 + delta, 5, 95)

    response = AnalysisResponse(
        score=score,
        summary=analysis_summary(score),
        breakdown=breakdown,
        suggestions=build_suggestions(
            breakdown, caption_length, hashtags, platform, language, intent_score),
        comparison=Comparison(benchmark=benchmark,
                              delta=delta, percentile=percentile),
        trending=Trending(
            audio=TRENDING_AUDIO.get(platform, TRENDING_AUDIO["tiktok"]),
            hashtags=TRENDING_TAGS.get(platform, TRENDING_TAGS["tiktok"]),
        ),
    )

    return response
