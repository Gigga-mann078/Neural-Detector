# -*- coding:utf-8 -*-
import dearpygui.dearpygui as dpg
import random
import math
import ctypes
import sys
import json
import os
import subprocess
import threading
from pathlib import Path
from web_searcher import WebSearcher

happpyend_path = Path(__file__).parent / "HapppyEnd"
if str(happpyend_path) not in sys.path:
    sys.path.insert(0, str(happpyend_path))

try:
    from HapppyEnd.LoLGic import SurgicalEnsembleDetector
    DETECTOR_AVAILABLE = True
    print("Detector loaded from HapppyEnd")
except ImportError as e:
    print(f"Failed to load detector: {e}")
    DETECTOR_AVAILABLE = False
    SurgicalEnsembleDetector = None


TEXTS = {
    "ru": {
        "title": "1Dat.Rya v2.0",
        "input_label": "ВВОД ТЕКСТА",
        "load_btn": "Загрузить файл",
        "results_label": "РЕЗУЛЬТАТЫ",
        "analyze_btn": "АНАЛИЗ",
        "ai_warning_btn": "Инфо",
        "history_btn": "ИСТОРИЯ",
        "settings_btn": "НАСТРОЙКИ",
        "save_btn": "СОХРАНИТЬ",
        "copy_btn": "КОПИРОВАТЬ",
        "clear_btn": "ОЧИСТИТЬ",
        "ready": "ГОТОВ К РАБОТЕ",
        "analyzing": "ПРОЦЕСС...",
        "enter_text": "ВВЕДИТЕ ТЕКСТ",
        "no_detector": "ДЕТЕКТОР НЕ ЗАГРУЖЕН",
        "engine_error": "ENGINE ERROR: ",
        "verdict_ai": "AI-GENERATED",
        "verdict_human": "HUMAN-WRITTEN",
        "verdict_uncertain": "UNCERTAIN / MIXED",
        "verdict_unknown": "UNKNOWN",
        "final_verdict": "FINAL VERDICT",
        "logic_analysis": "[!] LOGIC ANALYSIS:",
        "final_prob": "Final AI Probability:",
        "confidence": "System Confidence:",
        "algorithm_percentiles": "ALGORITHM PERCENTILES (MODULE TELEMETRY):",
        "raw_perplexity": "Raw Perplexity:",
        "language_info": "Language:",
        "words": "Words:",
        "file_loaded": "Загружен файл: ",
        "file_error": "Ошибка загрузки: ",
        "saved_to": "Сохранено в ",
        "copied": "Скопировано в буфер обмена",
        "cleared": "Поля очищены",
        "history_title": "ИСТОРИЯ АНАЛИЗОВ",
        "history_empty": "История пуста",
        "no_data": "Нет данных",
        "no_analysis": "Сначала выполните анализ",
        "settings_title": "Настройки",
        "lang_label": "Язык интерфейса:",
        "sound_label": "Звуковые сигналы",
        "save_settings_btn": "Сохранить",
        "cancel_btn": "Отмена",
        "settings_saved": "Настройки сохранены",
        "lang_set": "Язык установлен: Русский",
        "history_load": "Загрузить",
        "history_close": "Закрыть",
        "save_result_title": "Нет данных",
        "save_result_msg": "Нет результатов для сохранения",
        "standard_analysis": "Standard Statistical Analysis",
        "borderline": "[BORDERLINE] Gray area. Baseline stats are suspicious, but no hard module anomalies triggered.",
        "ipt_placeholder": "IPT не подключено",
    },
    "en": {
        "title": "1Dat.Rya v2.0",
        "input_label": "TEXT INPUT",
        "load_btn": "Load File",
        "results_label": "RESULTS",
        "analyze_btn": "ANALYZE",
        "ai_warning_btn": "Info",
        "history_btn": "HISTORY",
        "settings_btn": "SETTINGS",
        "save_btn": "SAVE",
        "copy_btn": "COPY",
        "clear_btn": "CLEAR",
        "ready": "READY",
        "analyzing": "PROCESS...",
        "enter_text": "ENTER TEXT",
        "no_detector": "DETECTOR NOT LOADED",
        "engine_error": "ENGINE ERROR: ",
        "verdict_ai": "AI-GENERATED",
        "verdict_human": "HUMAN-WRITTEN",
        "verdict_uncertain": "UNCERTAIN / MIXED",
        "verdict_unknown": "UNKNOWN",
        "final_verdict": "FINAL VERDICT",
        "logic_analysis": "[!] LOGIC ANALYSIS:",
        "final_prob": "Final AI Probability:",
        "confidence": "System Confidence:",
        "algorithm_percentiles": "ALGORITHM PERCENTILES (MODULE TELEMETRY):",
        "raw_perplexity": "Raw Perplexity:",
        "language_info": "Language:",
        "words": "Words:",
        "file_loaded": "Loaded file: ",
        "file_error": "Load error: ",
        "saved_to": "Saved to ",
        "copied": "Copied to clipboard",
        "cleared": "Cleared",
        "history_title": "ANALYSIS HISTORY",
        "history_empty": "History is empty",
        "no_data": "No data",
        "no_analysis": "Run analysis first",
        "settings_title": "Settings",
        "lang_label": "Interface language:",
        "sound_label": "Sound signals",
        "save_settings_btn": "Save",
        "cancel_btn": "Cancel",
        "settings_saved": "Settings saved",
        "lang_set": "Language set: English",
        "history_load": "Load",
        "history_close": "Close",
        "save_result_title": "No data",
        "save_result_msg": "No results to save",
        "standard_analysis": "Standard Statistical Analysis",
        "borderline": "[BORDERLINE] Gray area. Baseline stats are suspicious, but no hard module anomalies triggered.",
        "ipt_placeholder": "IPT not connected",
    }
}


def T(key, lang):
    return TEXTS.get(lang, TEXTS["ru"]).get(key, key)


class ConfigManager:
    def __init__(self):
        self.config_file = Path("config.json")
        self.config = self.load_config()

    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self.create_default_config()
        else:
            return self.create_default_config()

    def create_default_config(self):
        config = {
            "first_run": False,
            "privacy_accepted": True,
            "language": "ru",
            "theme": "dark",
            "sensitivity": 70,
            "use_perplexity": True,
            "use_patterns": True,
            "use_cpp": True,
            "sound_enabled": True,
            "show_verdict": True,
            "verdict_auto": True
        }
        self.save_config(config)
        return config

    def save_config(self, config=None):
        if config is not None:
            self.config = config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)


def get_screen_size():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    try:
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        if sw <= 0 or sh <= 0:
            raise ValueError
        return sw, sh
    except Exception:
        return 1920, 1080


class StarField:
    def __init__(self, width, height, num_stars=120):
        self.width = width
        self.height = height
        self.stars = []
        self.time = 0

        colors = [
            (180, 200, 255), (220, 220, 255), (255, 240, 220),
            (255, 220, 180), (255, 255, 255), (200, 220, 255),
        ]

        for _ in range(num_stars):
            self.stars.append({
                'x': random.uniform(0, width),
                'y': random.uniform(0, height),
                'size': random.uniform(0.8, 3.5),
                'brightness': random.uniform(0.3, 1.0),
                'color': random.choice(colors),
                'twinkle_speed': random.uniform(0.01, 0.05),
                'twinkle_phase': random.uniform(0, 2 * math.pi),
                'drift_x': random.uniform(-0.1, 0.1),
                'drift_y': random.uniform(-0.1, 0.1),
            })

    def update(self):
        self.time += 1
        for s in self.stars:
            s['x'] += s['drift_x']
            s['y'] += s['drift_y']
            if s['x'] < 0:           s['x'] = self.width
            if s['x'] > self.width:  s['x'] = 0
            if s['y'] < 0:           s['y'] = self.height
            if s['y'] > self.height: s['y'] = 0
            s['b'] = max(0.1, min(1.0, s['brightness'] +
                math.sin(self.time * s['twinkle_speed'] + s['twinkle_phase']) * 0.3))

    def draw(self, w, h):
        dpg.delete_item("stars_layer", children_only=True)
        for s in self.stars:
            b = s['b']
            r, g, bl = s['color']
            a = int(b * 255)
            dpg.draw_circle((s['x'], s['y']), s['size'],
                color=(r, g, bl, a), fill=(r, g, bl, a), parent="stars_layer")
            dpg.draw_circle((s['x'], s['y']), s['size'] * 2,
                color=(r, g, bl, int(a * 0.1)),
                fill=(r, g, bl, int(a * 0.03)), parent="stars_layer")


class PanelManager:
    def __init__(self):
        self.bottom_height  = 70
        self.bottom_trigger = 6
        self.right_width    = 340
        self.right_trigger  = 6
        self.speed          = 0.22

        self.bottom_y_cur   = 0.0
        self.right_x_cur    = 0.0
        self._first         = True

        self.force_right_frames = 0

        self.button_rects = []
        self.callbacks = {}
        self.app = None

    def set_app(self, app):
        self.app = app

    def set_callbacks(self, callbacks):
        self.callbacks = callbacks

    def flash_right(self, seconds=4.0, fps=60):
        self.force_right_frames = int(seconds * fps)

    def lang(self):
        return self.app.language if self.app else "ru"

    def result_text(self):
        return self.app.result_text if self.app else ""

    def tick(self, mx, my, ww, wh):
        if self._first:
            self.bottom_y_cur = float(wh - self.bottom_trigger)
            self.right_x_cur  = float(ww - self.right_trigger)
            self._first = False

        bottom_zone = my > wh - self.bottom_height - 20
        target_b = float(wh - self.bottom_height) if bottom_zone \
                   else float(wh - self.bottom_trigger)
        self.bottom_y_cur += (target_b - self.bottom_y_cur) * self.speed

        if self.force_right_frames > 0:
            self.force_right_frames -= 1
            right_zone = True
        else:
            right_zone = mx > ww - self.right_width - 20

        target_r = float(ww - self.right_width) if right_zone \
                   else float(ww - self.right_trigger)
        self.right_x_cur += (target_r - self.right_x_cur) * self.speed

    def handle_click(self, mx, my):
        for (x0, y0, x1, y1, key) in self.button_rects:
            if x0 <= mx <= x1 and y0 <= my <= y1:
                cb = self.callbacks.get(key)
                if cb:
                    cb()
                return True
        return False

    def draw(self, ww, wh):
        dpg.delete_item("panels_layer", children_only=True)
        self.button_rects = []
        self._draw_bottom(ww, wh)
        self._draw_right(ww, wh)

    def _draw_bottom(self, ww, wh):
        p = "panels_layer"
        y = self.bottom_y_cur
        lang = self.lang()
        cream  = (245, 242, 235, 235)
        border = (155, 155, 155, 210)

        dpg.draw_rectangle((0, y), (ww, wh + 1),
            color=border, fill=cream, thickness=1.5, parent=p)

        tx, ty = ww / 2, y + 5
        lc = (100, 100, 100, 170)
        for i in range(3):
            dpg.draw_line((tx - 13, ty + i*4), (tx + 13, ty + i*4),
                color=lc, thickness=1.5, parent=p)

        buttons = [
            (T("analyze_btn", lang),    "analyze"),
            (T("ai_warning_btn", lang), "ai_warning"),
            (T("history_btn", lang),    "history"),
            (T("settings_btn", lang),   "settings"),
            (T("save_btn", lang),       "save"),
            (T("copy_btn", lang),       "copy"),
            (T("clear_btn", lang),      "clear"),
        ]

        n       = len(buttons)
        btn_w   = 140
        btn_h   = 32
        gap     = 10
        total   = n * btn_w + (n - 1) * gap
        start_x = (ww - total) / 2
        btn_y   = y + 20

        for i, (label, key) in enumerate(buttons):
            bx = start_x + i * (btn_w + gap)
            dpg.draw_rectangle(
                (bx, btn_y), (bx + btn_w, btn_y + btn_h),
                color=(145, 145, 145, 210),
                fill=(248, 245, 240, 225),
                thickness=1.2, parent=p)
            dpg.draw_text(
                (bx + 8, btn_y + 8), label,
                color=(55, 55, 55, 220), size=13, parent=p)

            self.button_rects.append((bx, btn_y, bx + btn_w, btn_y + btn_h, key))

    def _draw_right(self, ww, wh):
        p = "panels_layer"
        x = self.right_x_cur
        lang = self.lang()
        cream  = (245, 242, 235, 225)
        border = (155, 155, 155, 210)

        dpg.draw_rectangle((x, 0), (ww + 1, wh),
            color=border, fill=cream, thickness=1.5, parent=p)

        lx_base, mid = x + 5, wh / 2
        lc = (110, 110, 110, 160)
        for i in range(3):
            dpg.draw_line((lx_base + i*4, mid - 13),
                          (lx_base + i*4, mid + 13),
                color=lc, thickness=1.5, parent=p)

        dpg.draw_text((x + 16, 18), T("results_label", lang),
            color=(55, 55, 55, 225), size=15, parent=p)
        dpg.draw_line((x + 12, 40), (ww - 8, 40),
            color=(155, 155, 155, 140), thickness=1, parent=p)

        lines = self.result_text().split('\n')
        for i, line in enumerate(lines[:35]):
            dpg.draw_text((x + 14, 54 + i * 18), line,
                color=(45, 45, 45, 205), size=12, parent=p)


def build_display_triplet(component_scores):
    items = list(component_scores.items())[:2]
    while len(items) < 2:
        items.append((f"SLOT_{len(items) + 1}", None))
    items.append(("IPT TECHNOLOGY", None))
    return items


def show_info_popup(title, message):
    tag = "info_popup"
    if dpg.does_item_exist(tag):
        dpg.delete_item(tag)
    with dpg.window(tag=tag, label=title, width=360, height=140,
                    pos=(260, 240), no_collapse=True):
        dpg.add_text(message, wrap=320)
        dpg.add_button(label="OK", callback=lambda: dpg.delete_item(tag))


def show_ai_warning(lang):
    if dpg.does_item_exist("ai_warning"):
        dpg.delete_item("ai_warning")

    title = "Information"
    lines = [
        "empty 0_0",
        ""
    ]

    with dpg.window(
        tag="ai_warning",
        label=title,
        width=400,
        height=230,
        pos=(250, 200),
        no_collapse=True
    ):
        for line in lines:
            if line == "":
                dpg.add_spacer(height=5)
            else:
                dpg.add_text(line, wrap=360, color=(220, 220, 220, 255))

        dpg.add_spacer(height=10)
        dpg.add_button(
            label="OK",
            callback=lambda: dpg.delete_item("ai_warning"),
            width=80,
            pos=(160, 190)
        )


def show_history_window(history, lang):
    if dpg.does_item_exist("history_window"):
        dpg.delete_item("history_window")

    with dpg.window(tag="history_window", label=T("history_title", lang),
                    width=480, height=360, pos=(200, 150)):
        for item in history:
            dpg.add_text(item)
        dpg.add_button(label=T("history_close", lang),
                       callback=lambda: dpg.delete_item("history_window"))


def show_settings_window(app):
    if dpg.does_item_exist("settings_window"):
        dpg.delete_item("settings_window")

    lang = app.language

    if lang == "ru":
        btn_save = "Сохранить"
        btn_cancel = "Отмена"
    else:
        btn_save = "Save"
        btn_cancel = "Cancel"

    with dpg.window(tag="settings_window", label=T("settings_title", lang),
                    width=400, height=300, pos=(250, 150)):
        dpg.add_text(T("lang_label", lang))
        dpg.add_radio_button(items=["Русский", "English"], tag="cfg_lang",
                             default_value="Русский" if lang == "ru" else "English",
                             horizontal=True)
        dpg.add_separator()
        dpg.add_text("FINAL VERDICT", color=(0, 200, 0, 255))
        dpg.add_checkbox(label="Show" if lang == "en" else "Показывать",
                 default_value=app.show_verdict, tag="cfg_show_verdict")
        dpg.add_checkbox(label="Auto mode" if lang == "en" else "Авто-режим",
                 default_value=app.verdict_auto, tag="cfg_verdict_auto",
                 callback=lambda s, a: (
                     dpg.configure_item("cfg_sensitivity", enabled=not a),
                     dpg.set_value("cfg_sensitivity", 50) if a else None
                 ))
        dpg.add_slider_int(label="Strictness" if lang == "en" else "Строгость",
                   tag="cfg_sensitivity",
                   default_value=app.sensitivity,
                   min_value=0, max_value=100,
                   enabled=not app.verdict_auto)

        def save_cfg():
            chosen = dpg.get_value("cfg_lang")
            app.language = "ru" if chosen == "Русский" else "en"
            app.show_verdict = dpg.get_value("cfg_show_verdict")
            app.sensitivity = dpg.get_value("cfg_sensitivity")
            app.verdict_auto = dpg.get_value("cfg_verdict_auto")
            app.config_manager.config["verdict_auto"] = app.verdict_auto

            app.config_manager.config.update({
                "language": app.language,
                "show_verdict": app.show_verdict,
                "sensitivity": app.sensitivity
            })
            app.config_manager.save_config()
            app.apply_language()
            app.update_status(T("settings_saved", app.language))
            dpg.delete_item("settings_window")

        dpg.add_button(label=btn_save, callback=save_cfg)
        dpg.add_button(label=btn_cancel, callback=lambda: dpg.delete_item("settings_window"))


class App:
    def __init__(self, panels):
        self.panels = panels
        self.config_manager = ConfigManager()

        self.language = self.config_manager.config.get("language", "ru")
        self.sensitivity = self.config_manager.config.get("sensitivity", 70)
        self.show_verdict = self.config_manager.config.get("show_verdict", True)
        self.verdict_auto = self.config_manager.config.get("verdict_auto", True)

        self.detector = None
        if DETECTOR_AVAILABLE:
            try:
                self.detector = SurgicalEnsembleDetector()
                print("Detector initialized")
            except Exception as e:
                print(f"Detector init error: {e}")

        self.history = []
        self.last_scores = {}
        self.result_text = ""
        self._last_web_results = []

        self._pending = {"done": False, "result": None, "error": None}
        self._busy = False

    def _(self, key):
        return T(key, self.language)

    def _get_input_text(self):
        if dpg.does_item_exist("text_input"):
            return dpg.get_value("text_input")
        return ""

    def update_status(self, message):
        if dpg.does_item_exist("status_bar"):
            dpg.set_value("status_bar", message)

    def apply_language(self):
        if dpg.does_item_exist("input_label_text"):
            dpg.set_value("input_label_text", self._("input_label"))
        if dpg.does_item_exist("load_btn"):
            dpg.configure_item("load_btn", label=self._("load_btn"))
        self.update_status(self._("ready"))

    def on_open_file(self, sender, app_data):
        file_path = app_data.get("file_path_name")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            dpg.set_value("text_input", text)
            self.update_status(f"{self._('file_loaded')}{os.path.basename(file_path)}")
        except Exception as e:
            self.update_status(f"{self._('file_error')}{str(e)}")

    def load_file(self):
        dpg.show_item("open_dialog")

    def analyze(self):
        text = self._get_input_text().strip()
        if not text:
            self.update_status(self._("enter_text"))
            return

        if not self.detector:
            self.update_status(self._("no_detector"))
            return

        if self._busy:
            return

        self.update_status(self._("analyzing"))
        self._busy = True
        self._pending = {"done": False, "result": None, "error": None}

        threading.Thread(target=self._analyze_worker, args=(text,), daemon=True).start()

    def _analyze_worker(self, text):
        try:
            raw_data = self.detector.analyze(text, detailed=True)

            base_prob = float(raw_data.get('ai_probability', 0.5))
            confidence = float(raw_data.get('confidence', 0.5))
            component_scores = raw_data.get('component_scores', {})

            perp_raw = raw_data.get('perplexity_raw')
            perp = float(perp_raw) if perp_raw is not None else 100.0

            patt = 0.0
            stylo = 0.0
            neural = 0.0
            for k, v in component_scores.items():
                if k.lower() == 'patterns': patt = float(v)
                if k.lower() == 'stylometry' or k.lower() == 'stylometric': stylo = float(v)
                if k.lower() == 'neural' or k.lower() == 'neural_network': neural = float(v)

            web_results = raw_data.get('web_results', [])

            if not web_results:
                try:
                    ws = WebSearcher()
                    web_data = ws.search(text, num_results=5)
                    web_results = web_data.get('all_results', [])
                except Exception as e:
                    print(f"WebSearcher error: {e}")
                    web_results = []

            web_match = False
            web_similarity = 0.0
            if web_results:
                best_web = web_results[0]
                web_similarity = best_web.get('similarity', 0.0)
                if web_similarity >= 0.80:
                    web_match = True

            word_count = raw_data.get('word_count', 0) or len(text.split())

            if word_count < 50:
                perp_threshold = 15.0
                neural_threshold = 0.75
            elif word_count < 100:
                perp_threshold = 20.0
                neural_threshold = 0.70
            elif word_count < 300:
                perp_threshold = 25.0
                neural_threshold = 0.60
            elif word_count < 600:
                perp_threshold = 30.0
                neural_threshold = 0.55
            else:
                perp_threshold = 35.0
                neural_threshold = 0.50

            final_prob = base_prob
            crit_insight = self._("standard_analysis")
            verdict = None

            if perp < perp_threshold and neural > neural_threshold:
                final_prob = 1.0
                crit_insight = (
                    f"[CRITICAL] LOW_PERPLEXITY ({perp:.1f}) + "
                    f"NEURAL_TRACK ({neural:.1%}). Auto-AI assignment.\n"
                    f"[THRESHOLDS] words={word_count}, "
                    f"perp<{perp_threshold}, neural>{neural_threshold:.2f}"
                )
                verdict = "AI"

            elif perp < perp_threshold or neural > neural_threshold:
                if perp < perp_threshold:
                    crit_insight = (
                        f"[WARNING] Low perplexity detected: {perp:.1f} "
                        f"(threshold: {perp_threshold}). Possible AI.\n"
                        f"[THRESHOLDS] words={word_count}, "
                        f"perp<{perp_threshold}, neural>{neural_threshold:.2f}"
                    )
                else:
                    crit_insight = (
                        f"[WARNING] Neural track detected: {neural:.1%} "
                        f"(threshold: {neural_threshold:.0%}). Possible AI.\n"
                        f"[THRESHOLDS] words={word_count}, "
                        f"perp<{perp_threshold}, neural>{neural_threshold:.2f}"
                    )
                verdict = "UNCERTAIN_AI"

            else:
                if 0.4 <= final_prob <= 0.6:
                    crit_insight = self._("borderline")

                crit_insight = (
                    f"{crit_insight}\n"
                    f"[THRESHOLDS] words={word_count}, "
                    f"perp<{perp_threshold}, neural>{neural_threshold:.2f}"
                )

                if self.verdict_auto:
                    if final_prob >= 0.75:
                        verdict = "AI"
                    elif final_prob >= 0.55:
                        verdict = "UNCERTAIN_AI"
                    elif final_prob >= 0.45:
                        verdict = "UNCERTAIN"
                    elif final_prob >= 0.25:
                        verdict = "UNCERTAIN_HUMAN"
                    else:
                        verdict = "HUMAN"
                else:
                    threshold = max(0.05, 1.0 - (self.sensitivity / 100.0) * 0.6)
                    if final_prob >= threshold:
                        verdict = "AI"
                    else:
                        verdict = "HUMAN"

            if web_match:
                crit_insight = (
                    f"[WEB MATCH] Text found in internet with {web_similarity:.1%} similarity.\n"
                    f"{crit_insight}"
                )

            processed_result = {
                'ai_probability': final_prob,
                'confidence': confidence,
                'verdict': verdict,
                'critical_point': crit_insight,
                'component_scores': component_scores,
                'perplexity_raw': perp,
                'language': raw_data.get('language', 'unknown'),
                'word_count': word_count,
                'web_results': web_results,
                'web_match': web_match,
                'web_similarity': web_similarity
            }

            self._pending["result"] = processed_result
            self._pending["done"] = True

        except Exception as e:
            self._pending["error"] = str(e)
            self._pending["done"] = True

    def poll_analysis(self):
        if not self._busy or not self._pending["done"]:
            return

        self._busy = False

        if self._pending["error"] is not None:
            self.update_status(f"{self._('engine_error')}{self._pending['error']}")
            return

        self._apply_result(self._pending["result"])

    def _apply_result(self, result):
        prob = result.get('ai_probability', 0.0)
        verdict = result.get('verdict', 'UNCERTAIN')
        crit_msg = result.get('critical_point', self._("standard_analysis"))
        component_scores = result.get('component_scores', {})
        web_results = result.get('web_results', [])
        self._last_web_results = web_results if web_results else []
        update_web_search_panel(self)

        themes = {
            "AI":              "AI-WRITTEN",
            "UNCERTAIN_AI":    "UNCERTAIN -> AI",
            "UNCERTAIN":       "UNCERTAIN / MIXED",
            "UNCERTAIN_HUMAN": "UNCERTAIN -> HUMAN",
            "HUMAN":           "HUMAN-WRITTEN",
        }
        label = themes.get(verdict, f"UNKNOWN ({verdict})")

        res_text = ""
        if self.show_verdict:
            res_text += "=" * 60 + "\n"
            res_text += f" {self._('final_verdict')}: {label}\n"
            res_text += "=" * 60 + "\n\n"

        res_text += f" {self._('logic_analysis')}\n"
        res_text += f" {crit_msg}\n"

        if result.get('web_match'):
            web_sim = result.get('web_similarity', 0.0)
            res_text += f"\n WEB MATCH: {web_sim:.1%} similarity\n"

        res_text += "-" * 60 + "\n\n"

        res_text += f"{self._('final_prob')} {prob:.1%}\n"
        res_text += f"{self._('confidence')} {result.get('confidence', 0.0):.1%}\n\n"

        triplet = build_display_triplet(component_scores)
        res_text += f"{self._('algorithm_percentiles')}\n"
        res_text += "-" * 45 + "\n"
        for algo, score in triplet:
            if score is None:
                res_text += f" {algo:15} | {self._('ipt_placeholder')}\n"
            else:
                bar_len = int(score * 20)
                bar = "#" * bar_len + "-" * (20 - bar_len)
                res_text += f" {algo:15} |{bar}| {score:.1%}\n"
        res_text += "\n"

        res_text += f"{self._('raw_perplexity')} {result.get('perplexity_raw', 'N/A')}\n"
        res_text += f"{self._('language_info')} {result.get('language')} | {self._('words')} {result.get('word_count')}\n"
        res_text += "=" * 60

        self.result_text = res_text
        self.last_scores = component_scores
        self.update_status(f"{self._('final_verdict')}: {label}")
        self.panels.flash_right(4.0)

    def open_history(self):
        if self.history:
            show_history_window(self.history, self.language)
        else:
            show_info_popup(self._("history_empty"), self._("no_data"))

    def open_settings(self):
        show_settings_window(self)

    def on_save_file(self, sender, app_data):
        path = app_data.get("file_path_name")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.result_text)
            self.update_status(f"{self._('saved_to')}{os.path.basename(path)}")
        except Exception as e:
            self.update_status(f"{self._('file_error')}{str(e)}")

    def save_result(self):
        result = self.result_text.strip()
        if not result:
            show_info_popup(self._("save_result_title"), self._("save_result_msg"))
            return
        dpg.show_item("save_dialog")

    def copy_result(self):
        result = self.result_text.strip()
        if result:
            dpg.set_clipboard_text(result)
            self.update_status(self._("copied"))

    def clear_all(self):
        dpg.set_value("text_input", "")
        self.result_text = ""
        self._last_web_results = []
        self.update_status(self._("cleared"))


def setup_font():
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/DejaVuSans.ttf",
    ]

    chosen = None
    for c in candidates:
        if os.path.exists(c):
            chosen = c
            break

    with dpg.font_registry():
        if chosen:
            default_font = dpg.add_font(chosen, 18)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=default_font)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default, parent=default_font)
            dpg.bind_font(default_font)


def show_web_search_panel(app, web_panel_x, web_panel_w, web_panel_h):
    lang = app.language

    dpg.add_text("Web Search",
                 tag="web_search_label",
                 pos=(web_panel_x, 30),
                 color=(100, 150, 255, 255))

    dpg.add_child_window(tag="web_search_panel",
                         width=web_panel_w,
                         height=web_panel_h,
                         pos=(web_panel_x, 50),
                         border=True,
                         autosize_x=False,
                         autosize_y=False)

    dpg.add_text("Waiting for analysis...",
                 tag="web_search_content",
                 parent="web_search_panel",
                 color=(150, 150, 150, 255),
                 wrap=web_panel_w - 20)


def copy_url_callback(sender, app_data, user_data):
    url = user_data
    if url:
        dpg.set_clipboard_text(url)


def update_web_search_panel(app):
    if not dpg.does_item_exist("web_search_panel"):
        return

    dpg.delete_item("web_search_panel", children_only=True)

    web_results = app._last_web_results
    lang = app.language

    if not web_results:
        dpg.add_text("No results",
                     parent="web_search_panel", color=(150, 150, 150, 255))
        return

    best = web_results[0]
    sim = best.get('similarity', 0.0)
    dpg.add_text(f"Similarity: {sim:.1%}",
                 parent="web_search_panel", color=(200, 200, 200, 255))
    dpg.add_separator(parent="web_search_panel")

    for idx, wr in enumerate(web_results[:5]):
        url = wr.get('url', '')
        sim_r = wr.get('similarity', 0.0)
        snippet = wr.get('snippet', '')[:60]
        sim_pct = int(sim_r * 100)

        with dpg.group(horizontal=True, parent="web_search_panel"):
            dpg.add_button(
                label=f"{sim_pct}%",
                small=True,
                tag=f"web_btn_{idx}",
                user_data=url,
                callback=copy_url_callback
            )
            dpg.add_text(f" {url[:40] if url else 'No URL'}", color=(100, 150, 255, 255))

        dpg.add_text(f"   {snippet}...", parent="web_search_panel", color=(160, 160, 160, 200))
        dpg.add_spacer(height=4, parent="web_search_panel")


def main():
    config_file = Path("config.json")
    need_privacy = True

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if config.get("privacy_accepted", False):
                need_privacy = False
        except Exception:
            pass

    if need_privacy:
        pp_path = Path(__file__).parent / "pp.py"
        if pp_path.exists():
            subprocess.run([sys.executable, str(pp_path)])
        else:
            print("pp.py not found")

    if not config_file.exists() or need_privacy:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if not config.get("privacy_accepted", False):
                sys.exit(0)
        else:
            sys.exit(0)

    dpg.create_context()

    with dpg.theme(tag="link_theme"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (100, 150, 255, 255))

    dpg.add_texture_registry(tag="textures")

    setup_font()

    sw, sh = get_screen_size()
    ww = int(sw * 0.95)
    wh = int(sh * 0.90)

    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize,       0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding,       0, 0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize,    0)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,         0, 0)
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg,            (8, 8, 18, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg,         (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab,       (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered,(0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (0, 0, 0, 0))
    dpg.bind_theme(global_theme)

    with dpg.theme() as input_theme:
        with dpg.theme_component(dpg.mvInputText):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (15, 15, 25, 200))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (210, 230, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (150, 150, 150, 150))
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1.0)

    dpg.create_viewport(
        title="1Dat.Rya",
        width=ww, height=wh,
        resizable=True, decorated=True,
        clear_color=(8, 8, 18, 255),
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()

    cw = dpg.get_viewport_client_width()
    ch = dpg.get_viewport_client_height()

    input_w = int(cw * 0.40)
    input_h = int(ch * 0.45)

    panels = PanelManager()
    app = App(panels)
    panels.set_app(app)
    panels.set_callbacks({
        "analyze":    app.analyze,
        "ai_warning": lambda: show_ai_warning(app.language),
        "history":    app.open_history,
        "settings":   app.open_settings,
        "save":       app.save_result,
        "copy":       app.copy_result,
        "clear":      app.clear_all,
    })

    with dpg.file_dialog(directory_selector=False, show=False,
                         callback=app.on_open_file, tag="open_dialog",
                         width=600, height=400):
        dpg.add_file_extension(".txt", color=(150, 255, 150, 255))
        dpg.add_file_extension(".*")

    with dpg.file_dialog(directory_selector=False, show=False,
                         callback=app.on_save_file, tag="save_dialog",
                         width=600, height=400, default_filename="result.txt"):
        dpg.add_file_extension(".txt", color=(150, 255, 150, 255))
        dpg.add_file_extension(".json", color=(150, 200, 255, 255))
        dpg.add_file_extension(".*")

    with dpg.window(tag="main",
                    no_title_bar=True, no_resize=True,
                    no_move=True, no_scrollbar=True,
                    no_collapse=True, no_background=False,
                    width=cw, height=ch, pos=(0, 0)):

        with dpg.drawlist(tag="canvas", width=cw, height=ch):
            dpg.add_draw_layer(tag="stars_layer")
            dpg.add_draw_layer(tag="panels_layer")

        dpg.add_text(app._("input_label"), tag="input_label_text",
             pos=(40, 30), color=(220, 220, 230, 230))

        dpg.add_button(label=app._("load_btn"), tag="load_btn",
               callback=lambda: app.load_file(),
               pos=(cw - 200, 30), width=160)

        dpg.add_input_text(tag="text_input", multiline=True,
                   width=input_w, height=input_h,
                   pos=(40, 55))

        web_panel_x = 40 + input_w + 15
        web_panel_w = int(cw * 0.22)
        web_panel_h = input_h
        show_web_search_panel(app, web_panel_x, web_panel_w, web_panel_h)
        dpg.bind_item_theme("text_input", input_theme)

        dpg.add_text(app._("ready"), tag="status_bar",
                     pos=(10, ch - 24), color=(160, 200, 160, 220))

    dpg.set_primary_window("main", True)

    stars = StarField(cw, ch)

    prev_w, prev_h = cw, ch

    while dpg.is_dearpygui_running():

        cw = dpg.get_viewport_client_width()
        ch = dpg.get_viewport_client_height()

        if cw != prev_w or ch != prev_h:
            prev_w, prev_h = cw, ch
            stars.width  = cw
            stars.height = ch
            dpg.configure_item("main",   width=cw, height=ch)
            dpg.configure_item("canvas", width=cw, height=ch)
            new_input_w = int(cw * 0.40)
            new_input_h = int(ch * 0.45)
            dpg.configure_item("text_input", width=new_input_w, height=new_input_h)
            dpg.configure_item("load_btn", pos=(cw - 200, 30))
            dpg.configure_item("status_bar", pos=(10, ch - 24))

            new_web_x = 40 + new_input_w + 15
            new_web_w = int(cw * 0.22)
            new_web_h = new_input_h
            dpg.configure_item("web_search_label", pos=(new_web_x, 30))
            dpg.configure_item("web_search_panel",
                               pos=(new_web_x, 50),
                               width=new_web_w,
                               height=new_web_h)

        mx, my = dpg.get_mouse_pos(local=False)

        stars.update()
        stars.draw(cw, ch)

        panels.tick(mx, my, cw, ch)
        panels.draw(cw, ch)

        if dpg.is_mouse_button_clicked(dpg.mvMouseButton_Left):
            try:
                panels.handle_click(mx, my)
            except Exception:
                import traceback
                traceback.print_exc()

        app.poll_analysis()

        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()