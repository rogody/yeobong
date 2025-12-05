"""
Cycle through emotions after each load completes (safe reloading).
Usage: python -m chatbot.app.ply_demo
"""

import sys
import itertools
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .ply_render import WebViewer, DEFAULT_BG_PLY

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESOURCES_DIR = PROJECT_ROOT / "Resources"
EMOTION_DIR = RESOURCES_DIR / "projply"
# 모든 감정/배경이 들어 있는 ssproj (배경, 카메라 포함)
ALL_EMO_SSPROJ = RESOURCES_DIR / "projply" / "all_emotions.ssproj"

# 감정 라벨 -> PLY 매핑 (필요에 맞게 수정 가능)
EMOTION_MAP = {
    "neutral": EMOTION_DIR / "jsw.ply",
    "happy": EMOTION_DIR / "happy.ply",
    "sad": EMOTION_DIR / "sad.ply",
    "surprise": EMOTION_DIR / "surprise.ply",
    "disgusted": EMOTION_DIR / "disgusted.ply",
    "upset": EMOTION_DIR / "upset.ply",
}

# 로드 완료 후 다음 감정으로 넘어가기 전 대기 시간 (ms)
EMOTION_INTERVAL_MS = 30000  # 30초


def build_paths(label: str) -> list[str]:
    # ssproj가 있을 경우 그 하나만 로드
    if ALL_EMO_SSPROJ.exists():
        return [str(ALL_EMO_SSPROJ)]
    # fallback: 배경 + 감정 PLY
    bg = str(DEFAULT_BG_PLY)
    emo = EMOTION_MAP.get(label, EMOTION_MAP["neutral"])
    return [bg, str(emo)]


def main():
    app = QApplication(sys.argv)
    viewer = WebViewer(auto_load=False)

    emotions = ["neutral", "happy", "sad", "surprise", "disgusted", "upset"]
    cycle = itertools.cycle(emotions)

    timer = QTimer()
    timer.setSingleShot(True)

    def on_loaded(ok: bool, label: str):
        try:
            viewer.browser.loadFinished.disconnect()
        except Exception:
            pass
        if ok:
            # ssproj에 모든 감정이 들어 있으면 visible 토글
            if ALL_EMO_SSPROJ.exists():
                viewer.set_visible_emotion(label, {k: v.name for k, v in EMOTION_MAP.items()})
            timer.start(EMOTION_INTERVAL_MS)

    def step():
        label = next(cycle)
        print(f"[cycle] loading emotion: {label}")
        try:
            viewer.browser.loadFinished.disconnect()
        except Exception:
            pass
        viewer.browser.loadFinished.connect(lambda ok, lbl=label: on_loaded(ok, lbl))
        viewer.load_scene(build_paths(label))

    timer.timeout.connect(step)
    step()  # 최초 실행

    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
