import sys
import os
import json
import webbrowser
from typing import Dict, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox, QTabWidget,
    QMenuBar, QMenu, QStatusBar, QDialog, QDialogButtonBox,
    QLineEdit, QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

class ConfigManager:
    """Manages configuration file operations"""

    @staticmethod
    def load_config(filepath: str) -> dict:
        """Load configuration from file"""
        config = {}
        current_section = None

        try:
            with open(filepath, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('#'):
                        if 'Section' in line:
                            current_section = line.split(':')[-1].strip()
                            config[current_section] = {}
                    elif '=' in line:
                        if current_section:
                            key, value = line.split('=', 1)
                            config[current_section][key.strip()] = value.strip()
            return config
        except Exception as e:
            raise Exception(f"Failed to load configuration: {str(e)}")

    @staticmethod
    def save_config(config: dict, filepath: str):
        """Save configuration to file"""
        try:
            with open(filepath, 'w') as file:
                for section, values in config.items():
                    file.write(f"############################################################################################\n")
                    file.write(f"# Section: {section}\n")
                    file.write(f"############################################################################################\n\n")

                    for key, value in values.items():
                        file.write(f"{key}={value}\n")
                    file.write("\n")
        except Exception as e:
            raise Exception(f"Failed to save configuration: {str(e)}")

class ConfigurationApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.config_manager = ConfigManager()
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Environment Configuration Manager")
        self.setMinimumSize(1200, 800)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create menu bar
        self.create_menu_bar()

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Add configuration tabs
        self.add_configuration_tabs()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Set initial status
        self.update_status("Ready")

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_config)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_config)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_config)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_config_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        validate_action = QAction("Validate All", self)
        validate_action.triggered.connect(self.validate_all)
        tools_menu.addAction(validate_action)

        export_action = QAction("Export Configuration", self)
        export_action.triggered.connect(self.export_config)
        tools_menu.addAction(export_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)

    def add_configuration_tabs(self):
        """Add all configuration section tabs"""
        # Import all section widgets
        from host_config import BroadseaHostSection
        from atlas_config import AtlasGUISection
        from webapi_config import WebAPISection
        from security_config import SecuritySection
        from datasource_config import DataSourceSection
        from build_config import BuildSection
        from monitoring_config import MonitoringSection

        # Create and add tabs
        self.sections = {
            "Host": BroadseaHostSection(),
            "Atlas": AtlasGUISection(),
            "WebAPI": WebAPISection(),
            "Security": SecuritySection(),
            "DataSource": DataSourceSection(),
            "Build": BuildSection(),
            "Monitoring": MonitoringSection()
        }

        for name, section in self.sections.items():
            self.tab_widget.addTab(section, name)

    def new_config(self):
        """Create new configuration"""
        if self.check_unsaved_changes():
            self.current_file = None
            for section in self.sections.values():
                section.reset_to_defaults()
            self.update_status("New configuration created")

    def open_config(self):
        """Open configuration file"""
        if not self.check_unsaved_changes():
            return

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Configuration",
            "",
            "Environment Files (*.env);;All Files (*.*)"
        )

        if filename:
            try:
                config = self.config_manager.load_config(filename)
                self.current_file = filename

                # Update each section with loaded configuration
                for section in self.sections.values():
                    section.load_config(config.get(section.section_name, {}))

                self.update_status(f"Loaded configuration from {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load configuration: {str(e)}"
                )

    def save_config(self):
        """Save current configuration"""
        if not self.current_file:
            self.save_config_as()
            return

        try:
            config = {}
            for section in self.sections.values():
                config[section.section_name] = section.get_config()

            self.config_manager.save_config(config, self.current_file)
            self.update_status(f"Saved configuration to {self.current_file}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save configuration: {str(e)}"
            )

    def save_config_as(self):
        """Save configuration to new file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration As",
            "",
            "Environment Files (*.env);;All Files (*.*)"
        )

        if filename:
            self.current_file = filename
            self.save_config()

    def validate_all(self):
        """Validate all configuration sections"""
        issues = []
        for name, section in self.sections.items():
            section_issues = section.validate()
            if section_issues:
                issues.extend([f"{name}: {issue}" for issue in section_issues])

        if issues:
            QMessageBox.warning(
                self,
                "Validation Issues",
                "The following issues were found:\n\n" + "\n".join(issues)
            )
        else:
            QMessageBox.information(
                self,
                "Validation Success",
                "All configuration sections are valid!"
            )

    def export_config(self):
        """Export configuration to different formats"""
        formats = {
            "JSON": (".json", self.export_json),
            "YAML": (".yaml", self.export_yaml),
            "Docker Compose": (".yml", self.export_docker_compose)
        }

        dialog = ExportDialog(list(formats.keys()), self)
        if dialog.exec():
            format_name = dialog.get_selected_format()
            if format_name in formats:
                extension, export_func = formats[format_name]

                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    f"Export as {format_name}",
                    "",
                    f"{format_name} Files (*{extension});;All Files (*.*)"
                )

                if filename:
                    try:
                        export_func(filename)
                        self.update_status(f"Exported configuration as {format_name}")
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Export Error",
                            f"Failed to export configuration: {str(e)}"
                        )

    def export_json(self, filename):
        """Export configuration as JSON"""
        config = {}
        for section in self.sections.values():
            config[section.section_name] = section.get_config()

        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)

    def export_yaml(self, filename):
        """Export configuration as YAML"""
        try:
            import yaml
            config = {}
            for section in self.sections.values():
                config[section.section_name] = section.get_config()

            with open(filename, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except ImportError:
            raise Exception("PyYAML is required for YAML export")

    def export_docker_compose(self, filename):
        """Export configuration as Docker Compose file"""
        services = {
            "atlas": {
                "image": f"ohdsi/atlas:{self.sections['Atlas'].get_config()['ATLAS_VERSION']}",
                "ports": [f"{self.sections['Atlas'].get_config()['ATLAS_PORT']}:8080"],
                "environment": self.sections['Atlas'].get_config(),
                "depends_on": ["postgres", "webapi"]
            },
            "webapi": {
                "image": f"ohdsi/webapi:{self.sections['WebAPI'].get_config()['WEBAPI_VERSION']}",
                "ports": [f"{self.sections['WebAPI'].get_config()['WEBAPI_PORT']}:8080"],
                "environment": self.sections['WebAPI'].get_config(),
                "depends_on": ["postgres"]
            },
            "postgres": {
                "image": "postgres:13",
                "ports": ["5432:5432"],
                "environment": {
                    "POSTGRES_USER": self.sections['DataSource'].get_config()['DATASOURCE_DB_USER'],
                    "POSTGRES_PASSWORD": self.sections['DataSource'].get_config()['DATASOURCE_DB_PASS'],
                    "POSTGRES_DB": self.sections['DataSource'].get_config()['DATASOURCE_DB_NAME']
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"]
            }
        }

        compose_config = {
            "version": "3.8",
            "services": services,
            "volumes": {
                "postgres_data": None
            }
        }

        with open(filename, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Environment Configuration Manager",
            "Environment Configuration Manager v1.0\n\n"
            "A tool for managing OHDSI environment configurations."
        )

    def show_documentation(self):
        """Show documentation"""
        docs_url = "https://github.com/OHDSI/Broadsea/wiki"
        try:
            webbrowser.open(docs_url)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Documentation Error",
                f"Failed to open documentation: {str(e)}\n\n"
                f"Please visit {docs_url} manually."
            )

    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes"""
        if not self.current_file:
            return True

        try:
            current_config = {}
            for section in self.sections.values():
                current_config[section.section_name] = section.get_config()

            saved_config = self.config_manager.load_config(self.current_file)

            if current_config != saved_config:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                return reply == QMessageBox.StandardButton.Yes

        except Exception:
            # If there's any error reading the saved file, assume it's safe to proceed
            pass

        return True

    def update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.showMessage(message)

class ExportDialog(QDialog):
    """Dialog for selecting export format"""

    def __init__(self, formats, parent=None):
        super().__init__(parent)
        self.formats = formats
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Export Configuration")
        layout = QVBoxLayout(self)

        # Format selection
        layout.addWidget(QLabel("Select Export Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.formats)
        layout.addWidget(self.format_combo)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_format(self) -> str:
        """Get selected format"""
        return self.format_combo.currentText()

def main():
    app = QApplication(sys.argv)
    window = ConfigurationApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
