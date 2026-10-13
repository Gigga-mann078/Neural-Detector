# -*- coding: utf-8 -*-
import dearpygui.dearpygui as dpg
import json
import os
import sys
from pathlib import Path


def setup_font():
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/DejaVuSans.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            with dpg.font_registry():
                font = dpg.add_font(c, 18)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=font)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default, parent=font)
                dpg.bind_font(font)
            return


TEXTS = {
    "ru": {
        "title": "ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ",
        "content": (
            "Добро пожаловать в 1Dat.Rya.\n\n"
            "Бета-тест приложения. Автор: Gigga-mann078.\n\n"
            "Программа обрабатывает введённый текст локально на вашем устройстве. "
            "Статистика аналитических модулей (Perplexity, Stylometrics, "
            "Neural Networks, Pattern Recognition) используется исключительно "
            "для вычисления вероятности генерации текста искусственным интеллектом.\n\n"
            "ВНИМАНИЕ: Программа НЕ гарантирует 100% точность анализа. "
            "Результаты носят рекомендательный характер.\n\n"
            "Нажимая 'Принять', вы соглашаетесь на обработку данных "
            "в рамках работы приложения."
        ),
        "lang_label": "Язык:",
        "accept": "Принять",
        "decline": "Отказаться",
    },
    "en": {
        "title": "PRIVACY POLICY",
        "content": (
            "Welcome to 1Dat.Rya.\n\n"
            "Beta test. Author: Gigga-mann078.\n\n"
            "The program processes the entered text locally on your device. "
            "The statistics of the analysis modules (Perplexity, Stylometrics, "
            "Neural Networks, Pattern Recognition) are used solely to calculate "
            "the probability of AI text generation.\n\n"
            "WARNING: The program does NOT guarantee 100% accuracy. "
            "Results are advisory only.\n\n"
            "By clicking 'Accept', you agree to the data processing "
            "within the application scope."
        ),
        "lang_label": "Language:",
        "accept": "Accept",
        "decline": "Decline",
    }
}

current_lang = "en"


def refresh_texts():
    global current_lang
    t = TEXTS[current_lang]

    dpg.set_value("title_text", t["title"])
    dpg.set_value("content_text", t["content"])
    dpg.set_value("lang_label", t["lang_label"])
    dpg.configure_item("btn_accept", label=t["accept"])
    dpg.configure_item("btn_decline", label=t["decline"])


def on_lang_change(sender, app_data):
    global current_lang
    if app_data == "Русский":
        current_lang = "ru"
    else:
        current_lang = "en"
    refresh_texts()


def show_privacy_policy():
    global current_lang

    config_file = Path("config.json")

    def accept():
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception:
                config = {}
        else:
            config = {}

        config["privacy_accepted"] = True
        config["first_run"] = False
        config["language"] = current_lang
        config.setdefault("theme", "dark")
        config.setdefault("sensitivity", 70)
        config.setdefault("show_verdict", True)
        config.setdefault("verdict_auto", True)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        dpg.stop_dearpygui()

    def decline():
        dpg.stop_dearpygui()
        sys.exit(0)

    dpg.create_context()

    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 10, 10, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (200, 200, 200, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 45, 45, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 60, 60, 255))
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 10)
    dpg.bind_theme(theme)

    dpg.create_viewport(
        title="Privacy Policy / Политика конфиденциальности",
        width=520, height=520,
        resizable=False, decorated=True,
    )

    setup_font()

    with dpg.window(tag="main", no_title_bar=True, no_resize=True, no_move=True):
        dpg.add_text("PRIVACY POLICY", tag="title_text", color=(0, 255, 0, 255))
        dpg.add_spacer(height=10)

        with dpg.group(horizontal=True):
            dpg.add_text("Language:", tag="lang_label")
            dpg.add_radio_button(
                items=["Русский", "English"],
                tag="lang_select",
                default_value="English",
                horizontal=True,
                callback=on_lang_change
            )

        dpg.add_spacer(height=10)

        with dpg.child_window(width=470, height=320, border=True):
            dpg.add_text(TEXTS["en"]["content"], tag="content_text",
                         wrap=440, color=(200, 200, 200, 255))

        dpg.add_spacer(height=15)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Decline", tag="btn_decline",
                           callback=decline, width=180, height=35)
            dpg.add_spacer(width=10)
            dpg.add_button(label="Accept", tag="btn_accept",
                           callback=accept, width=180, height=35)

    dpg.set_primary_window("main", True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    show_privacy_policy()