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


class Reasoning(BaseModel):
    hook: str
    pacing: str
    thumbnail: str
    caption: str
    trend: str


class Signals(BaseModel):
    hook_visual: Optional[int]
    pace_visual: Optional[int]
    brightness: Optional[int]
    contrast: Optional[int]
    duration_seconds: Optional[float]


class Confidence(BaseModel):
    label: str
    score: int


class AnalysisResponse(BaseModel):
    score: int
    summary: str
    breakdown: Breakdown
    suggestions: List[str]
    rewrites: List[str]
    reasons: Reasoning
    hook_panel: str
    signals: Signals
    confidence: Confidence
    takeaways: List[str]
    comparison: Comparison
    trending: Trending


BENCHMARK_RANGES = {
    "tiktok": {"video": (64, 86), "image": (58, 80)},
    "instagram": {"video": (62, 84), "image": (56, 78)},
    "youtube": {"video": (63, 85), "image": (57, 79)},
    "default": {"video": (60, 82), "image": (55, 77)},
}


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


def score_hook(
    caption: str,
    file_size_mb: Optional[float],
    hook_visual: Optional[int],
) -> int:
    text = caption.lower()
    hit = any(word in text for word in HOOK_WORDS)
    hook_base = 72 if hit else 52
    size_penalty = 0
    if file_size_mb is not None:
        size_penalty = max(0, (file_size_mb - 8) * 2)
    base_score = clamp(hook_base - size_penalty)
    if hook_visual is None:
        return base_score
    return clamp((base_score * 0.6) + (hook_visual * 0.4))


def score_pacing(
    file_size_mb: Optional[float],
    duration_seconds: Optional[float],
    platform: str,
    pace_visual: Optional[int],
) -> int:
    if duration_seconds is None:
        if file_size_mb is None:
            return 55
        target = 7 if platform == "tiktok" else 9
        diff = abs(file_size_mb - target)
        base = clamp(90 - diff * 6)
        if pace_visual is None:
            return base
        return clamp((base * 0.6) + (pace_visual * 0.4))

    target_seconds = 18 if platform == "tiktok" else 24
    diff = abs(duration_seconds - target_seconds)
    base = clamp(92 - diff * 2.2)
    if pace_visual is None:
        return base
    return clamp((base * 0.6) + (pace_visual * 0.4))


def score_thumbnail(
    image_size: Optional[tuple[int, int]],
    platform: str,
    brightness: Optional[int],
    contrast: Optional[int],
) -> int:
    if image_size is None:
        return 58

    width, height = image_size
    if height == 0:
        return 58

    ratio = width / height
    target_ratio = 9 / 16 if platform in {"tiktok", "instagram"} else 9 / 16
    ratio_score = 100 - abs(ratio - target_ratio) * 220
    pixel_score = 100 - max(0, 720 - min(width, height)) * 0.05
    base_score = clamp((ratio_score * 0.6) + (pixel_score * 0.4))
    if brightness is None or contrast is None:
        return base_score
    visual_score = clamp((brightness * 0.4) + (contrast * 0.6))
    return clamp((base_score * 0.6) + (visual_score * 0.4))


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
    hook_visual: Optional[int],
    pace_visual: Optional[int],
    brightness: Optional[int],
    contrast: Optional[int],
) -> List[str]:
    suggestions: List[str] = []
    platform_label = PLATFORM_LABELS.get(platform, platform.title())

    if breakdown.hook < 65:
        suggestions.append(
            "Open with a sharper first line like a bold claim or a surprise result.")
        suggestions.extend(hook_examples(platform, language))
        if hook_visual is not None and hook_visual < 55:
            suggestions.append(
                "Increase motion or visual change in the first 3 seconds to keep attention.")
    if breakdown.pacing < 65:
        suggestions.append(
            "Tighten pacing with quicker cuts in the first 5 seconds.")
        if pace_visual is not None and pace_visual < 55:
            suggestions.append(
                "Add jump cuts or on-screen text changes every 2 to 3 seconds.")
    if breakdown.thumbnail < 65:
        suggestions.append(
            "Use a high-contrast thumbnail with one focal subject.")
        if brightness is not None and brightness < 40:
            suggestions.append(
                "Boost lighting so the subject stands out from the background.")
        if contrast is not None and contrast < 40:
            suggestions.append(
                "Increase contrast to make the thumbnail readable on mobile.")
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


def extract_hashtags(caption: str, limit: int = 3) -> List[str]:
    tags: List[str] = []
    for token in caption.split():
        if token.startswith("#") and len(tags) < limit:
            tags.append(token)
    return tags


def generate_rewrites(
    caption: str,
    platform: str,
    goal: str,
    language: str,
    hashtags: int,
) -> List[str]:
    platform_label = PLATFORM_LABELS.get(platform, platform.title())
    base_tags = extract_hashtags(caption)
    tag_suffix = f" {' '.join(base_tags)}" if base_tags else ""
    goal_line = {
        "reach": "Share this with a friend who needs it.",
        "engagement": "Comment your biggest struggle below.",
        "conversions": "Try this today and report back.",
    }.get(goal, "Save this for later.")

    if not caption.strip():
        caption = "Here is the idea in one line"

    templates = [
        f"Hook: {caption.strip()} {goal_line}{tag_suffix}",
        f"{platform_label} tip: {caption.strip()}\n{goal_line}{tag_suffix}",
        f"Before/After: {caption.strip()}\nSave this for later.{tag_suffix}",
    ]

    if language != "en":
        templates.append(
            f"Local + English: {caption.strip()} | Quick tip in English here.{tag_suffix}"
        )

    return templates[:3]


def analysis_summary(score: int) -> str:
    if score >= 85:
        return "High viral potential. Only minor edits needed to maximize reach."
    if score >= 70:
        return "Solid foundations with a few quick wins to boost performance."
    if score >= 55:
        return "Average potential. Focus on hook and pacing to lift retention."
    return "Low potential today. Strengthen the hook and simplify the message."


def build_reasons(
    caption_length: int,
    hashtags: int,
    intent_score: int,
    hook_visual: Optional[int],
    pace_visual: Optional[int],
    brightness: Optional[int],
    contrast: Optional[int],
    duration_seconds: Optional[float],
    target_seconds: Optional[int],
    trend_matches: int,
) -> Reasoning:
    hook_reason = "Hook score uses caption cues and early visual change."
    if hook_visual is not None:
        hook_reason = f"First 3s change score: {hook_visual}/100."

    pacing_reason = "Pacing score uses duration and visual change."
    if duration_seconds is not None and target_seconds is not None:
        pacing_reason = f"Duration {duration_seconds:.1f}s vs target {target_seconds}s."
        if pace_visual is not None:
            pacing_reason += f" Visual pace score {pace_visual}/100."

    thumbnail_reason = "Thumbnail score uses aspect ratio and resolution."
    if brightness is not None and contrast is not None:
        thumbnail_reason = f"Brightness {brightness}/100, contrast {contrast}/100."

    caption_reason = (
        f"Length {caption_length} chars, {hashtags} hashtags, intent {intent_score}/100."
    )

    trend_reason = f"Trending tag matches: {trend_matches}."

    return Reasoning(
        hook=hook_reason,
        pacing=pacing_reason,
        thumbnail=thumbnail_reason,
        caption=caption_reason,
        trend=trend_reason,
    )


def compute_confidence(
    has_media: bool,
    duration_seconds: Optional[float],
    hook_visual: Optional[int],
    pace_visual: Optional[int],
    brightness: Optional[int],
    contrast: Optional[int],
) -> Confidence:
    score = 40
    if has_media:
        score += 20
    if duration_seconds is not None:
        score += 15
    if hook_visual is not None:
        score += 10
    if pace_visual is not None:
        score += 10
    if brightness is not None and contrast is not None:
        score += 5

    score = clamp(score)
    if score >= 80:
        label = "High"
    elif score >= 60:
        label = "Medium"
    else:
        label = "Low"

    return Confidence(label=label, score=score)


def build_takeaways(breakdown: Breakdown, platform: str) -> List[str]:
    items = []
    platform_label = PLATFORM_LABELS.get(platform, platform.title())
    scores = {
        "hook": breakdown.hook,
        "pacing": breakdown.pacing,
        "thumbnail": breakdown.thumbnail,
        "caption": breakdown.caption,
        "trend": breakdown.trend,
    }
    lowest = sorted(scores.items(), key=lambda item: item[1])[:3]
    for metric, score in lowest:
        if metric == "hook":
            items.append(
                "Fix the first 3 seconds with a stronger hook statement.")
        elif metric == "pacing":
            items.append(
                "Speed up early pacing with quicker cuts or text beats.")
        elif metric == "thumbnail":
            items.append(
                "Increase thumbnail clarity with brighter lighting and contrast.")
        elif metric == "caption":
            items.append(
                "Tighten the caption and add a clear CTA to boost engagement.")
        elif metric == "trend":
            items.append(
                f"Add a trending audio/hashtag combo for {platform_label}.")

    if not items:
        items.append(
            "Strong baseline. A/B test hook and thumbnail to push reach.")
    return items


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
    brightness: Optional[int] = Form(None),
    contrast: Optional[int] = Form(None),
    duration_seconds: Optional[float] = Form(None),
    hook_visual: Optional[int] = Form(None),
    pace_visual: Optional[int] = Form(None),
    media: Optional[UploadFile] = File(None),
) -> AnalysisResponse:
    media_bytes: Optional[bytes] = None
    image_size: Optional[tuple[int, int]] = None
    file_size_mb: Optional[float] = None

    if media is not None:
        media_bytes = await media.read()
        file_size_mb = len(media_bytes) / (1024 * 1024)

    media_type = "image"
    if media is not None and media.content_type:
        if media.content_type.startswith("video/"):
            media_type = "video"
        elif media.content_type.startswith("image/"):
            media_type = "image"

    if image_width and image_height:
        image_size = (image_width, image_height)

    caption_length, hashtags = caption_metrics(caption)
    language = detect_language(caption)
    intent_score = detect_intent(caption)

    target_seconds = 18 if platform == "tiktok" else 24
    breakdown = Breakdown(
        hook=score_hook(caption, file_size_mb, hook_visual),
        pacing=score_pacing(file_size_mb, duration_seconds,
                            platform, pace_visual),
        thumbnail=score_thumbnail(image_size, platform, brightness, contrast),
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

    seed_input = f"{caption}-{media.filename if media else ''}-{file_size_mb}-{platform}-{media_type}"
    rng = random.Random(hash_seed(seed_input))
    platform_ranges = BENCHMARK_RANGES.get(
        platform, BENCHMARK_RANGES["default"])
    bench_low, bench_high = platform_ranges.get(media_type, (60, 82))
    benchmark = clamp(rng.randint(bench_low, bench_high))
    delta = score - benchmark
    percentile = clamp(50 + delta, 5, 95)
    trend_matches = sum(
        tag.lower() in caption.lower() for tag in TRENDING_TAGS.get(platform, [])
    )

    hook_panel = "First 3 seconds change score not available for images."
    if hook_visual is not None:
        hook_panel = f"First 3 seconds change score: {hook_visual}/100."

    response = AnalysisResponse(
        score=score,
        summary=analysis_summary(score),
        breakdown=breakdown,
        suggestions=build_suggestions(
            breakdown,
            caption_length,
            hashtags,
            platform,
            language,
            intent_score,
            hook_visual,
            pace_visual,
            brightness,
            contrast,
        ),
        rewrites=generate_rewrites(
            caption, platform, goal, language, hashtags),
        reasons=build_reasons(
            caption_length,
            hashtags,
            intent_score,
            hook_visual,
            pace_visual,
            brightness,
            contrast,
            duration_seconds,
            target_seconds if duration_seconds is not None else None,
            trend_matches,
        ),
        hook_panel=hook_panel,
        signals=Signals(
            hook_visual=hook_visual,
            pace_visual=pace_visual,
            brightness=brightness,
            contrast=contrast,
            duration_seconds=duration_seconds,
        ),
        confidence=compute_confidence(
            media is not None,
            duration_seconds,
            hook_visual,
            pace_visual,
            brightness,
            contrast,
        ),
        takeaways=build_takeaways(breakdown, platform),
        comparison=Comparison(benchmark=benchmark,
                              delta=delta, percentile=percentile),
        trending=Trending(
            audio=TRENDING_AUDIO.get(platform, TRENDING_AUDIO["tiktok"]),
            hashtags=TRENDING_TAGS.get(platform, TRENDING_TAGS["tiktok"]),
        ),
    )

    return response
