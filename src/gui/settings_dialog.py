# src/gui/settings_dialog.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (QWidget, QDialog, QFormLayout, QComboBox,
                             QSpinBox, QCheckBox, QPushButton, QColorDialog, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QMessageBox, QDialogButtonBox, QLabel, QSlider, QLineEdit)

from src.config.config import config, APP_NAME
from src.ocr.ocr import OcrProcessor

THEMES = {
    "Nazeka": {
        "color_background": "#2E2E2E", "color_foreground": "#F0F0F0",
        "color_highlight_word": "#88D8FF", "color_highlight_reading": "#90EE90",
        "background_opacity": 245,
    },
    "Celestial Indigo": {
        "color_background": "#281E50", "color_foreground": "#EAEFF5",
        "color_highlight_word": "#D4C58A", "color_highlight_reading": "#B5A2D4",
        "background_opacity": 245,
    },
    "Neutral Slate": {
        "color_background": "#5D5C5B", "color_foreground": "#EFEBE8",
        "color_highlight_word": "#A3B8A3", "color_highlight_reading": "#A3B8A3",
        "background_opacity": 245,
    },
    "Academic": {
        "color_background": "#FDFBF7", "color_foreground": "#212121",
        "color_highlight_word": "#8C2121", "color_highlight_reading": "#005A9C",
        "background_opacity": 245,
    },
    "Custom": {}
}

class SettingsDialog(QDialog):
    def __init__(self, ocr_processor: OcrProcessor, parent=None):
        super().__init__(parent)
        self.ocr_processor = ocr_processor
        self.setWindowTitle(f"{APP_NAME} Settings")
        self.setWindowIcon(QIcon("icon.ico"))
        layout = QVBoxLayout(self)
        general_group = QGroupBox("General")
        general_layout = QFormLayout()
        self.hotkey_combo = QComboBox(); self.hotkey_combo.addItems(['shift', 'ctrl', 'alt']); self.hotkey_combo.setCurrentText(config.hotkey)
        general_layout.addRow("Hotkey:", self.hotkey_combo)
        self.ocr_provider_combo = QComboBox()
        self.ocr_provider_combo.addItems(self.ocr_processor.available_providers.keys())
        self.ocr_provider_combo.setCurrentText(config.ocr_provider)
        general_layout.addRow("OCR Provider:", self.ocr_provider_combo)
        self.quality_combo = QComboBox(); self.quality_combo.addItems(['fast', 'balanced', 'quality']); self.quality_combo.setCurrentText(config.quality_mode)
        general_layout.addRow("Quality Mode:", self.quality_combo)
        self.max_lookup_spin = QSpinBox(); self.max_lookup_spin.setRange(5, 100); self.max_lookup_spin.setValue(config.max_lookup_length)
        general_layout.addRow("Max Lookup Length:", self.max_lookup_spin)
        self.auto_scan_check = QCheckBox()
        self.auto_scan_check.setChecked(config.auto_scan_mode)
        general_layout.addRow("Auto Scan Mode:", self.auto_scan_check)
        self.auto_scan_no_hotkey_check = QCheckBox()
        self.auto_scan_no_hotkey_check.setChecked(config.auto_scan_mode_lookups_without_hotkey)
        general_layout.addRow("Lookups without Hotkey (in Auto Scan):", self.auto_scan_no_hotkey_check)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        theme_group = QGroupBox("Popup")
        theme_layout = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.setCurrentText(config.theme_name if config.theme_name in THEMES else "Custom")
        self.theme_combo.currentTextChanged.connect(self._apply_theme)
        theme_layout.addRow("Theme:", self.theme_combo)
        self.opacity_slider_container = QWidget()
        opacity_layout = QHBoxLayout(self.opacity_slider_container)
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 255)
        self.opacity_slider.setValue(config.background_opacity)
        self.opacity_label = QLabel(f"{config.background_opacity}")
        self.opacity_label.setMinimumWidth(30)
        self.opacity_slider.valueChanged.connect(lambda val: self.opacity_label.setText(str(val)))
        self.opacity_slider.valueChanged.connect(self._mark_as_custom)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        theme_layout.addRow("Background Opacity:", self.opacity_slider_container)
        theme_layout.addRow(QLabel("Customize Colors:"))
        self.color_widgets = {}
        color_settings_map = {"Background": "color_background", "Foreground": "color_foreground",
                              "Highlight Word": "color_highlight_word", "Highlight Reading": "color_highlight_reading"}
        for name, key in color_settings_map.items():
            btn = QPushButton(getattr(config, key))
            btn.clicked.connect(lambda _, k=key, b=btn: self.pick_color(k, b))
            self.color_widgets[key] = btn
            theme_layout.addRow(f"  {name}:", btn)
        theme_layout.addRow(QLabel("Customize Layout:"))
        self.font_family_edit = QLineEdit(config.font_family)
        theme_layout.addRow("  Font Family:", self.font_family_edit)
        self.font_size_header_spin = QSpinBox();
        self.font_size_header_spin.setRange(8, 72)
        self.font_size_header_spin.setValue(config.font_size_header)
        theme_layout.addRow("  Font Size (Header):", self.font_size_header_spin)
        self.font_size_def_spin = QSpinBox()
        self.font_size_def_spin.setRange(8, 72)
        self.font_size_def_spin.setValue(config.font_size_definitions)
        theme_layout.addRow("  Font Size (Definitions):", self.font_size_def_spin)
        self.compact_check = QCheckBox(); self.compact_check.setChecked(config.compact_mode)
        theme_layout.addRow("  Compact Mode:", self.compact_check)
        self.hide_deconj_check = QCheckBox(); self.hide_deconj_check.setChecked(config.hide_deconjugation)
        theme_layout.addRow("  Hide Deconjugation:", self.hide_deconj_check)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._update_color_buttons()
        

    def _mark_as_custom(self):
        if self.theme_combo.currentText() != "Custom":
            self.theme_combo.setCurrentText("Custom")


    def _apply_theme(self, theme_name):
        if theme_name in THEMES and theme_name != "Custom":
            theme_data = THEMES[theme_name]
            for key, value in theme_data.items():
                setattr(config, key, value)
            self._update_color_buttons()
            self.opacity_slider.setValue(config.background_opacity)


    def _update_color_buttons(self):
        for key, btn in self.color_widgets.items():
            color_hex = getattr(config, key)
            btn.setText(color_hex)
            q_color = QColor(color_hex)
            text_color = "#000000" if q_color.lightness() > 127 else "#FFFFFF"
            btn.setStyleSheet(f"background-color: {color_hex}; color: {text_color};")


    def pick_color(self, key, btn):
        color = QColorDialog.getColor(QColor(getattr(config, key)), self)
        if color.isValid():
            setattr(config, key, color.name())
            self._update_color_buttons()
            self._mark_as_custom()


    def save_and_accept(self):
        selected_provider = self.ocr_provider_combo.currentText()
        if selected_provider != config.ocr_provider:
            self.ocr_processor.switch_provider(selected_provider)
        config.ocr_provider = selected_provider
        config.hotkey = self.hotkey_combo.currentText()
        config.quality_mode = self.quality_combo.currentText()
        config.max_lookup_length = self.max_lookup_spin.value()
        config.auto_scan_mode = self.auto_scan_check.isChecked()
        config.auto_scan_mode_lookups_without_hotkey = self.auto_scan_no_hotkey_check.isChecked()
        config.compact_mode = self.compact_check.isChecked()
        config.hide_deconjugation = self.hide_deconj_check.isChecked()
        config.theme_name = self.theme_combo.currentText()
        config.background_opacity = self.opacity_slider.value()
        config.font_family = self.font_family_edit.text()
        config.font_size_header = self.font_size_header_spin.value()
        config.font_size_definitions = self.font_size_def_spin.value()
        config.save()
        QMessageBox.information(self, "Settings Saved", "Settings have been saved.\nPlease restart the application for all changes to take effect.")
        self.accept()