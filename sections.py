import sys
import os
from typing import Dict, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QScrollArea, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt

@dataclass
class ConfigField:
    """Represents a configuration field with its metadata"""
    key: str
    default_value: str
    description: str
    options: list = None  # For dropdown fields
    is_file_path: bool = False
    is_secret: bool = False

class BroadseaHostSection:
    """Handles the Broadsea Host configuration section"""

    def __init__(self):
        self.section_name = "Broadsea Host Configuration"
        self.fields = {
            "DOCKER_ARCH": ConfigField(
                key="DOCKER_ARCH",
                default_value="linux/amd64",
                description="Docker architecture (linux/amd64 or linux/arm64 for Mac Silicon)",
                options=["linux/amd64", "linux/arm64"]
            ),
            "BROADSEA_HOST": ConfigField(
                key="BROADSEA_HOST",
                default_value="127.0.0.1",
                description="Host URL (without http part)"
            ),
            "HTTP_TYPE": ConfigField(
                key="HTTP_TYPE",
                default_value="http",
                description="HTTP protocol type",
                options=["http", "https"]
            ),
            "BROADSEA_CERTS_FOLDER": ConfigField(
                key="BROADSEA_CERTS_FOLDER",
                default_value="./certs",
                description="Certificate folder path",
                is_file_path=True
            ),
            "GITHUB_PAT_SECRET_FILE": ConfigField(
                key="GITHUB_PAT_SECRET_FILE",
                default_value="./secrets/github_pat",
                description="GitHub Personal Access Token file path",
                is_file_path=True,
                is_secret=True
            )
        }

class EnvConfigApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.sections = {}
        self.input_widgets = {}
        self.setup_ui()

        # Initialize sections
        self.broadsea_section = BroadseaHostSection()
        self.add_section(self.broadsea_section)

    def setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Docker Environment Configuration")
        self.setMinimumSize(1000, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Add action buttons
        button_layout = QHBoxLayout()
        load_button = QPushButton("Load Configuration")
        save_button = QPushButton("Save Configuration")
        validate_button = QPushButton("Validate Configuration")

        load_button.clicked.connect(self.load_config)
        save_button.clicked.connect(self.save_config)
        validate_button.clicked.connect(self.validate_config)

        button_layout.addWidget(load_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(validate_button)
        layout.addLayout(button_layout)

    def add_section(self, section):
        """Add a new configuration section to the UI"""
        group = QGroupBox(section.section_name)
        group_layout = QVBoxLayout()
        group.setLayout(group_layout)

        # Add fields for this section
        for field_name, field_config in section.fields.items():
            field_layout = QHBoxLayout()

            # Add label with description tooltip
            label = QLabel(field_name)
            label.setToolTip(field_config.description)
            field_layout.addWidget(label)

            # Create appropriate input widget based on field type
            if field_config.options:
                input_widget = QComboBox()
                input_widget.addItems(field_config.options)
                input_widget.setCurrentText(field_config.default_value)
            else:
                input_widget = QLineEdit()
                input_widget.setText(field_config.default_value)
                if field_config.is_secret:
                    input_widget.setEchoMode(QLineEdit.EchoMode.Password)

            # Add browse button for file paths
            if field_config.is_file_path:
                browse_button = QPushButton("Browse...")
                browse_button.clicked.connect(
                    lambda checked, w=input_widget: self.browse_file_path(w)
                )
                field_layout.addWidget(browse_button)

            field_layout.addWidget(input_widget)
            group_layout.addLayout(field_layout)

            # Store reference to input widget
            self.input_widgets[field_name] = input_widget

        self.scroll_layout.addWidget(group)
        self.sections[section.section_name] = section

    def browse_file_path(self, input_widget):
        """Open file dialog for path selection"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Directory", os.path.expanduser("~")
        )
        if path:
            input_widget.setText(path)

    def load_config(self):
        """Load configuration from a file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Configuration File",
            "",
            "Environment Files (*.env);;All Files (*.*)"
        )

        if not filename:
            return

        try:
            with open(filename, 'r') as file:
                config_data = {}
                for line in file:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config_data[key.strip()] = value.strip().strip('"')

                # Update UI with loaded values
                for key, widget in self.input_widgets.items():
                    if key in config_data:
                        if isinstance(widget, QComboBox):
                            widget.setCurrentText(config_data[key])
                        else:
                            widget.setText(config_data[key])

            QMessageBox.information(self, "Success", "Configuration loaded successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load configuration: {str(e)}")

    def save_config(self):
        """Save configuration to a file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration File",
            "",
            "Environment Files (*.env);;All Files (*.*)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w') as file:
                for section_name, section in self.sections.items():
                    file.write(f"############################################################################################\n")
                    file.write(f"# {section_name}\n")
                    file.write(f"############################################################################################\n\n")

                    for field_name, field_config in section.fields.items():
                        widget = self.input_widgets[field_name]
                        if isinstance(widget, QComboBox):
                            value = widget.currentText()
                        else:
                            value = widget.text()

                        file.write(f"# {field_config.description}\n")
                        file.write(f"{field_name}={value}\n\n")

            QMessageBox.information(self, "Success", "Configuration saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    def validate_config(self):
        """Validate the current configuration"""
        issues = []

        for section_name, section in self.sections.items():
            for field_name, field_config in section.fields.items():
                widget = self.input_widgets[field_name]
                value = widget.currentText() if isinstance(widget, QComboBox) else widget.text()

                # Check required fields
                if not value and not field_config.is_secret:
                    issues.append(f"{field_name} is required")

                # Check file paths exist
                if field_config.is_file_path and value:
                    if not os.path.exists(os.path.dirname(value)):
                        issues.append(f"Directory for {field_name} does not exist: {value}")

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
                "All configuration values are valid!"
            )

def main():
    app = QApplication(sys.argv)
    window = EnvConfigApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

import sys
import os
from typing import Dict, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QScrollArea, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt

# Reuse the ConfigField dataclass from previous section
@dataclass
class ConfigField:
    key: str
    default_value: str
    description: str
    options: list = None
    is_file_path: bool = False
    is_secret: bool = False
    is_boolean: bool = False

class AtlasGUISection:
    """Handles the Atlas GUI configuration section"""

    def __init__(self):
        self.section_name = "Atlas GUI Configuration"
        self.fields = {
            "ATLAS_INSTANCE_NAME": ConfigField(
                key="ATLAS_INSTANCE_NAME",
                default_value="Broadsea",
                description="Name of the Atlas instance"
            ),
            "ATLAS_COHORT_COMPARISON_RESULTS_ENABLED": ConfigField(
                key="ATLAS_COHORT_COMPARISON_RESULTS_ENABLED",
                default_value="false",
                description="Enable cohort comparison results",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_USER_AUTH_ENABLED": ConfigField(
                key="ATLAS_USER_AUTH_ENABLED",
                default_value="false",
                description="Enable user authentication",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_PLP_RESULTS_ENABLED": ConfigField(
                key="ATLAS_PLP_RESULTS_ENABLED",
                default_value="false",
                description="Enable Patient Level Prediction results",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_USE_EXECUTION_ENGINE": ConfigField(
                key="ATLAS_USE_EXECUTION_ENGINE",
                default_value="false",
                description="Enable Execution Engine for Estimation module",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_DISABLE_BROWSER_CHECK": ConfigField(
                key="ATLAS_DISABLE_BROWSER_CHECK",
                default_value="false",
                description="Disable browser compatibility warning",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_ENABLE_TAGGING_SECTION": ConfigField(
                key="ATLAS_ENABLE_TAGGING_SECTION",
                default_value="false",
                description="Show Tagging module in navigation",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_CACHE_SOURCES": ConfigField(
                key="ATLAS_CACHE_SOURCES",
                default_value="false",
                description="Enable source caching",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_POLL_INTERVAL": ConfigField(
                key="ATLAS_POLL_INTERVAL",
                default_value="60000",
                description="Polling interval in milliseconds"
            ),
            "ATLAS_ENABLE_SKIP_LOGIN": ConfigField(
                key="ATLAS_ENABLE_SKIP_LOGIN",
                default_value="false",
                description="Enable skip login option",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_VIEW_PROFILE_DATES": ConfigField(
                key="ATLAS_VIEW_PROFILE_DATES",
                default_value="false",
                description="Enable profile dates viewing",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_ENABLE_COSTS": ConfigField(
                key="ATLAS_ENABLE_COSTS",
                default_value="false",
                description="Enable cost analysis features",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_SUPPORT_URL": ConfigField(
                key="ATLAS_SUPPORT_URL",
                default_value="https://github.com/ohdsi/atlas/issues",
                description="Support URL for Atlas"
            ),
            "ATLAS_SUPPORT_MAIL": ConfigField(
                key="ATLAS_SUPPORT_MAIL",
                default_value="atlasadmin@your.org",
                description="Support email address"
            ),
            "ATLAS_DEFAULT_LOCALE": ConfigField(
                key="ATLAS_DEFAULT_LOCALE",
                default_value="en",
                description="Default language locale",
                options=["en", "fr", "de", "es", "nl", "kr", "cn", "ru", "it", "ja"]
            ),
            "ATLAS_ENABLE_PERSON_COUNT": ConfigField(
                key="ATLAS_ENABLE_PERSON_COUNT",
                default_value="true",
                description="Enable person count display",
                options=["true", "false"],
                is_boolean=True
            ),
            "ATLAS_ENABLE_TERMS_AND_CONDITIONS": ConfigField(
                key="ATLAS_ENABLE_TERMS_AND_CONDITIONS",
                default_value="true",
                description="Enable terms and conditions",
                options=["true", "false"],
                is_boolean=True
            )
        }

class EnvConfigApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.sections = {}
        self.input_widgets = {}
        self.setup_ui()

        # Initialize sections
        self.atlas_section = AtlasGUISection()
        self.add_section(self.atlas_section)

    def add_section(self, section):
        """Add a new configuration section to the UI"""
        group = QGroupBox(section.section_name)
        group_layout = QVBoxLayout()
        group.setLayout(group_layout)

        # Add fields for this section
        for field_name, field_config in section.fields.items():
            field_layout = QHBoxLayout()

            # Add label with description tooltip
            label = QLabel(field_name)
            label.setToolTip(field_config.description)
            field_layout.addWidget(label)

            # Create appropriate input widget based on field type
            if field_config.is_boolean:
                input_widget = QComboBox()
                input_widget.addItems(["true", "false"])
                input_widget.setCurrentText(field_config.default_value)
            elif field_config.options:
                input_widget = QComboBox()
                input_widget.addItems(field_config.options)
                input_widget.setCurrentText(field_config.default_value)
            else:
                input_widget = QLineEdit()
                input_widget.setText(field_config.default_value)
                if field_config.is_secret:
                    input_widget.setEchoMode(QLineEdit.EchoMode.Password)

            field_layout.addWidget(input_widget)

            # Add a help icon or button with tooltip
            help_label = QLabel("ℹ️")
            help_label.setToolTip(field_config.description)
            field_layout.addWidget(help_label)

            group_layout.addLayout(field_layout)

            # Store reference to input widget
            self.input_widgets[field_name] = input_widget

        self.scroll_layout.addWidget(group)
        self.sections[section.section_name] = section

    def validate_atlas_config(self):
        """Validate Atlas-specific configuration"""
        issues = []

        # Get Atlas section
        atlas_section = self.sections.get("Atlas GUI Configuration")
        if not atlas_section:
            return ["Atlas GUI Configuration section not found"]

        # Validate URL format
        support_url = self.input_widgets["ATLAS_SUPPORT_URL"].text()
        if not support_url.startswith(("http://", "https://")):
            issues.append("Support URL must start with http:// or https://")

        # Validate email format
        support_email = self.input_widgets["ATLAS_SUPPORT_MAIL"].text()
        if "@" not in support_email or "." not in support_email:
            issues.append("Invalid support email format")

        # Validate polling interval
        try:
            poll_interval = int(self.input_widgets["ATLAS_POLL_INTERVAL"].text())
            if poll_interval < 1000:  # Less than 1 second
                issues.append("Polling interval should be at least 1000 milliseconds")
        except ValueError:
            issues.append("Polling interval must be a number")

        return issues

    def validate_config(self):
        """Validate the current configuration"""
        issues = []

        # Validate Atlas-specific configuration
        atlas_issues = self.validate_atlas_config()
        issues.extend(atlas_issues)

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
                "All Atlas GUI configuration values are valid!"
            )

def main():
    app = QApplication(sys.argv)
    window = EnvConfigApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

import sys
import os
import re
from typing import Dict, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QScrollArea, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QComboBox, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt

@dataclass
class ConfigField:
    key: str
    default_value: str
    description: str
    options: list = None
    is_file_path: bool = False
    is_secret: bool = False
    is_boolean: bool = False
    validation_pattern: str = None

class WebAPISection:
    """Handles the WebAPI configuration section"""

    def __init__(self):
        self.section_name = "WebAPI Configuration"
        self.fields = self._initialize_fields()

    def _initialize_fields(self):
        """Initialize all WebAPI configuration fields"""
        return {
            # Schema and Database Configuration
            "FLYWAY_BASELINE_ON_MIGRATE": ConfigField(
                key="FLYWAY_BASELINE_ON_MIGRATE",
                default_value="true",
                description="Enable Flyway baseline on migrate for pre-filled WebAPI schema",
                options=["true", "false"],
                is_boolean=True
            ),

            # Logging Configuration
            "WEBAPI_LOGGING_LEVEL_ROOT": ConfigField(
                key="WEBAPI_LOGGING_LEVEL_ROOT",
                default_value="info",
                description="Root logging level for the entire application",
                options=["trace", "debug", "info", "warn", "error"]
            ),
            "WEBAPI_LOGGING_LEVEL_ORG_OHDSI": ConfigField(
                key="WEBAPI_LOGGING_LEVEL_ORG_OHDSI",
                default_value="info",
                description="Logging level for OHDSI libraries",
                options=["trace", "debug", "info", "warn", "error"]
            ),
            "WEBAPI_LOGGING_LEVEL_ORG_APACHE_SHIRO": ConfigField(
                key="WEBAPI_LOGGING_LEVEL_ORG_APACHE_SHIRO",
                default_value="warn",
                description="Logging level for Shiro authentication library",
                options=["trace", "debug", "info", "warn", "error"]
            ),

            # Database Connection
            "WEBAPI_DATASOURCE_URL": ConfigField(
                key="WEBAPI_DATASOURCE_URL",
                default_value="jdbc:postgresql://broadsea-atlasdb:5432/postgres",
                description="Database connection URL",
                validation_pattern=r"^jdbc:(postgresql|mysql|sqlserver|oracle):\/\/[\w\-\.]+:\d+\/[\w\-]+"
            ),
            "WEBAPI_DATASOURCE_USERNAME": ConfigField(
                key="WEBAPI_DATASOURCE_USERNAME",
                default_value="postgres",
                description="Database username"
            ),
            "WEBAPI_DATASOURCE_PASSWORD_FILE": ConfigField(
                key="WEBAPI_DATASOURCE_PASSWORD_FILE",
                default_value="./secrets/webapi/WEBAPI_DATASOURCE_PASSWORD",
                description="Path to database password file",
                is_file_path=True,
                is_secret=True
            ),
            "WEBAPI_DATASOURCE_OHDSI_SCHEMA": ConfigField(
                key="WEBAPI_DATASOURCE_OHDSI_SCHEMA",
                default_value="webapi",
                description="OHDSI schema name"
            ),

            # JDBC and Java Configuration
            "WEBAPI_ADDITIONAL_JDBC_FILE_PATH": ConfigField(
                key="WEBAPI_ADDITIONAL_JDBC_FILE_PATH",
                default_value="../jdbc/none.jar",
                description="Additional JDBC driver jar file path",
                is_file_path=True
            ),
            "WEBAPI_CACERTS_FILE": ConfigField(
                key="WEBAPI_CACERTS_FILE",
                default_value="../cacerts",
                description="Custom Java Keystore file path",
                is_file_path=True
            ),

            # Caching Configuration
            "CACHE_GENERATION_INVALIDAFTERDAYS": ConfigField(
                key="CACHE_GENERATION_INVALIDAFTERDAYS",
                default_value="30",
                description="Days until cohort cache invalidation (-1 to disable)",
                validation_pattern=r"^-1|\d+$"
            ),
            "CACHE_GENERATION_CLEANUPINTERVAL": ConfigField(
                key="CACHE_GENERATION_CLEANUPINTERVAL",
                default_value="3600000",
                description="Cache cleanup interval in milliseconds",
                validation_pattern=r"^\d+$"
            ),

            # Internationalization
            "I18N_ENABLED": ConfigField(
                key="I18N_ENABLED",
                default_value="true",
                description="Enable multiple language support",
                options=["true", "false"],
                is_boolean=True
            ),

            # Execution Engine
            "EXECUTIONENGINE_URL": ConfigField(
                key="EXECUTIONENGINE_URL",
                default_value="http://broadsea-arachne-execution-engine:8888/api/v1",
                description="Arachne execution engine URL",
                validation_pattern=r"^https?:\/\/[\w\-\.]+:\d+\/.*$"
            ),

            # Snowflake Configuration
            "WEBAPI_CDM_SNOWFLAKE_PRIVATE_KEY_FILE": ConfigField(
                key="WEBAPI_CDM_SNOWFLAKE_PRIVATE_KEY_FILE",
                default_value="./secrets/webapi/CDM_SNOWFLAKE_PRIVATE_KEY",
                description="Snowflake private key file path",
                is_file_path=True,
                is_secret=True
            )
        }

class WebAPIConfigWidget(QWidget):
    """Widget for WebAPI configuration section"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.section = WebAPISection()
        self.input_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI for WebAPI configuration"""
        layout = QVBoxLayout(self)

        # Create subsections
        self.add_subsection(layout, "Database Configuration", [
            "WEBAPI_DATASOURCE_URL",
            "WEBAPI_DATASOURCE_USERNAME",
            "WEBAPI_DATASOURCE_PASSWORD_FILE",
            "WEBAPI_DATASOURCE_OHDSI_SCHEMA"
        ])

        self.add_subsection(layout, "Logging Configuration", [
            "WEBAPI_LOGGING_LEVEL_ROOT",
            "WEBAPI_LOGGING_LEVEL_ORG_OHDSI",
            "WEBAPI_LOGGING_LEVEL_ORG_APACHE_SHIRO"
        ])

        self.add_subsection(layout, "Caching Configuration", [
            "CACHE_GENERATION_INVALIDAFTERDAYS",
            "CACHE_GENERATION_CLEANUPINTERVAL"
        ])

        self.add_subsection(layout, "Additional Configuration", [
            "FLYWAY_BASELINE_ON_MIGRATE",
            "I18N_ENABLED",
            "EXECUTIONENGINE_URL",
            "WEBAPI_ADDITIONAL_JDBC_FILE_PATH",
            "WEBAPI_CACERTS_FILE",
            "WEBAPI_CDM_SNOWFLAKE_PRIVATE_KEY_FILE"
        ])

    def add_subsection(self, parent_layout, title, field_keys):
        """Add a subsection with specified fields"""
        group = QGroupBox(title)
        group_layout = QVBoxLayout()

        for key in field_keys:
            field_config = self.section.fields[key]
            field_layout = QHBoxLayout()

            # Label
            label = QLabel(field_config.key)
            label.setToolTip(field_config.description)
            field_layout.addWidget(label)

            # Input widget
            if field_config.options:
                input_widget = QComboBox()
                input_widget.addItems(field_config.options)
                input_widget.setCurrentText(field_config.default_value)
            else:
                input_widget = QLineEdit()
                input_widget.setText(field_config.default_value)
                if field_config.is_secret:
                    input_widget.setEchoMode(QLineEdit.EchoMode.Password)

            # Add file browser button if needed
            if field_config.is_file_path:
                browse_button = QPushButton("Browse...")
                browse_button.clicked.connect(
                    lambda checked, w=input_widget: self.browse_file_path(w)
                )
                field_layout.addWidget(browse_button)

            field_layout.addWidget(input_widget)

            # Help icon
            help_label = QLabel("ℹ️")
            help_label.setToolTip(field_config.description)
            field_layout.addWidget(help_label)

            group_layout.addLayout(field_layout)
            self.input_widgets[key] = input_widget

        group.setLayout(group_layout)
        parent_layout.addWidget(group)

    def browse_file_path(self, input_widget):
        """Handle file/directory browsing"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Directory", os.path.expanduser("~")
        )
        if path:
            input_widget.setText(path)

    def validate(self):
        """Validate WebAPI configuration"""
        issues = []

        for field_name, widget in self.input_widgets.items():
            field_config = self.section.fields[field_name]
            value = widget.currentText() if isinstance(widget, QComboBox) else widget.text()

            # Required field check
            if not value and not field_config.is_secret:
                issues.append(f"{field_name} is required")

            # Pattern validation
            if field_config.validation_pattern and value:
                if not re.match(field_config.validation_pattern, value):
                    issues.append(f"{field_name} has invalid format")

            # File path validation
            if field_config.is_file_path and value:
                parent_dir = os.path.dirname(value)
                if not os.path.exists(parent_dir):
                    issues.append(f"Directory for {field_name} does not exist: {parent_dir}")

            # Specific validations
            if field_name == "CACHE_GENERATION_INVALIDAFTERDAYS":
                try:
                    days = int(value)
                    if days < -1:
                        issues.append("Cache invalidation days must be -1 or greater")
                except ValueError:
                    issues.append("Cache invalidation days must be a number")

            elif field_name == "CACHE_GENERATION_CLEANUPINTERVAL":
                try:
                    interval = int(value)
                    if interval < 1000:
                        issues.append("Cache cleanup interval must be at least 1000ms")
                except ValueError:
                    issues.append("Cache cleanup interval must be a number")

        return issues

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("WebAPI Configuration")
    window.setMinimumSize(800, 600)

    webapi_widget = WebAPIConfigWidget()
    window.setCentralWidget(webapi_widget)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

import sys
import os
import re
from typing import Dict, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QScrollArea, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QComboBox, QCheckBox, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt

@dataclass
class ConfigField:
    key: str
    default_value: str
    description: str
    options: list = None
    is_file_path: bool = False
    is_secret: bool = False
    is_boolean: bool = False
    validation_pattern: str = None
    provider_specific: str = None  # Indicates which security provider this field belongs to

class SecuritySection:
    """Handles the security configuration section"""

    def __init__(self):
        self.section_name = "Security Configuration"
        self.fields = self._initialize_fields()

    def _initialize_fields(self):
        """Initialize all security configuration fields"""
        return {
            # Atlas Security Provider Configuration
            "ATLAS_SECURITY_PROVIDER_TYPE": ConfigField(
                key="ATLAS_SECURITY_PROVIDER_TYPE",
                default_value="none",
                description="Security provider type",
                options=["none", "ad", "ldap", "kerberos", "openid", "cas", "oauth", "iap", "db"],
                provider_specific=None
            ),
            "ATLAS_SECURITY_PROVIDER_NAME": ConfigField(
                key="ATLAS_SECURITY_PROVIDER_NAME",
                default_value="none",
                description="Display name for the security provider",
                provider_specific=None
            ),
            "ATLAS_SECURITY_ICON": ConfigField(
                key="ATLAS_SECURITY_ICON",
                default_value="fa-cubes",
                description="Font-awesome icon name for the provider",
                provider_specific=None
            ),
            "ATLAS_SECURITY_USE_FORM": ConfigField(
                key="ATLAS_SECURITY_USE_FORM",
                default_value="false",
                description="Enable form-based authentication",
                options=["true", "false"],
                is_boolean=True,
                provider_specific=None
            ),

            # WebAPI Security Configuration
            "WEBAPI_SECURITY_PROVIDER": ConfigField(
                key="WEBAPI_SECURITY_PROVIDER",
                default_value="DisabledSecurity",
                description="WebAPI security provider type",
                options=["DisabledSecurity", "AtlasRegularSecurity"],
                provider_specific=None
            ),
            "SECURITY_TOKEN_EXPIRATION": ConfigField(
                key="SECURITY_TOKEN_EXPIRATION",
                default_value="28800",
                description="Security token expiration in seconds",
                validation_pattern=r"^\d+$",
                provider_specific=None
            ),

            # Database Authentication
            "SECURITY_AUTH_JDBC_ENABLED": ConfigField(
                key="SECURITY_AUTH_JDBC_ENABLED",
                default_value="false",
                description="Enable database authentication",
                options=["true", "false"],
                is_boolean=True,
                provider_specific="db"
            ),
            "SECURITY_DB_DATASOURCE_SCHEMA": ConfigField(
                key="SECURITY_DB_DATASOURCE_SCHEMA",
                default_value="webapi_security",
                description="Security database schema",
                provider_specific="db"
            ),

            # LDAP Configuration
            "SECURITY_AUTH_LDAP_ENABLED": ConfigField(
                key="SECURITY_AUTH_LDAP_ENABLED",
                default_value="false",
                description="Enable LDAP authentication",
                options=["true", "false"],
                is_boolean=True,
                provider_specific="ldap"
            ),
            "SECURITY_LDAP_URL": ConfigField(
                key="SECURITY_LDAP_URL",
                default_value="ldap://broadsea-openldap:1389",
                description="LDAP server URL",
                validation_pattern=r"^ldaps?:\/\/[\w\-\.]+:\d+$",
                provider_specific="ldap"
            ),

            # Active Directory Configuration
            "SECURITY_AUTH_AD_ENABLED": ConfigField(
                key="SECURITY_AUTH_AD_ENABLED",
                default_value="false",
                description="Enable Active Directory authentication",
                options=["true", "false"],
                is_boolean=True,
                provider_specific="ad"
            ),
            "SECURITY_AD_URL": ConfigField(
                key="SECURITY_AD_URL",
                default_value="",
                description="Active Directory server URL",
                provider_specific="ad"
            ),

            # OAuth Configuration
            "SECURITY_AUTH_OAUTH_ENABLED": ConfigField(
                key="SECURITY_AUTH_OAUTH_ENABLED",
                default_value="false",
                description="Enable OAuth authentication",
                options=["true", "false"],
                is_boolean=True,
                provider_specific="oauth"
            ),
            "SECURITY_OAUTH_CALLBACK_UI": ConfigField(
                key="SECURITY_OAUTH_CALLBACK_UI",
                default_value="http://localhost/Atlas/#/welcome",
                description="OAuth callback URL for UI",
                validation_pattern=r"^https?:\/\/[\w\-\.]+(?::\d+)?\/.*$",
                provider_specific="oauth"
            ),

            # OpenID Configuration
            "SECURITY_AUTH_OPENID_ENABLED": ConfigField(
                key="SECURITY_AUTH_OPENID_ENABLED",
                default_value="false",
                description="Enable OpenID authentication",
                options=["true", "false"],
                is_boolean=True,
                provider_specific="openid"
            ),

            # Kerberos Configuration
            "SECURITY_AUTH_KERBEROS_ENABLED": ConfigField(
                key="SECURITY_AUTH_KERBEROS_ENABLED",
                default_value="false",
                description="Enable Kerberos authentication",
                options=["true", "false"],
                is_boolean=True,
                provider_specific="kerberos"
            ),

            # CAS Configuration
            "SECURITY_AUTH_CAS_ENABLED": ConfigField(
                key="SECURITY_AUTH_CAS_ENABLED",
                default_value="false",
                description="Enable CAS authentication",
                options=["true", "false"],
                is_boolean=True,
                provider_specific="cas"
            ),

            # Google IAP Configuration
            "SECURITY_AUTH_GOOGLEIAP_ENABLED": ConfigField(
                key="SECURITY_AUTH_GOOGLEIAP_ENABLED",
                default_value="false",
                description="Enable Google Identity-Aware Proxy",
                options=["true", "false"],
                is_boolean=True,
                provider_specific="iap"
            )
        }

class SecurityConfigWidget(QWidget):
    """Widget for security configuration section"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.section = SecuritySection()
        self.input_widgets = {}
        self.provider_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI for security configuration"""
        layout = QVBoxLayout(self)

        # Add main security settings
        main_group = QGroupBox("General Security Settings")
        main_layout = QVBoxLayout()

        # Add provider selector
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Security Provider:")
        self.provider_selector = QComboBox()
        self.provider_selector.addItems([
            "None", "Database", "LDAP", "Active Directory",
            "OAuth", "OpenID", "Kerberos", "CAS", "Google IAP"
        ])
        self.provider_selector.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_selector)
        main_layout.addLayout(provider_layout)

        # Add general security fields
        general_fields = [
            "ATLAS_SECURITY_PROVIDER_TYPE",
            "ATLAS_SECURITY_PROVIDER_NAME",
            "ATLAS_SECURITY_ICON",
            "ATLAS_SECURITY_USE_FORM",
            "WEBAPI_SECURITY_PROVIDER",
            "SECURITY_TOKEN_EXPIRATION"
        ]

        for field_name in general_fields:
            self.add_field(main_layout, field_name)

        main_group.setLayout(main_layout)
        layout.addWidget(main_group)

        # Create stacked widget for provider-specific settings
        self.provider_stack = QStackedWidget()
        layout.addWidget(self.provider_stack)

        # Add provider-specific settings pages
        self.setup_provider_pages()

    def setup_provider_pages(self):
        """Setup pages for each security provider"""
        providers = {
            "none": [],
            "db": ["SECURITY_AUTH_JDBC_ENABLED", "SECURITY_DB_DATASOURCE_SCHEMA"],
            "ldap": ["SECURITY_AUTH_LDAP_ENABLED", "SECURITY_LDAP_URL"],
            "ad": ["SECURITY_AUTH_AD_ENABLED", "SECURITY_AD_URL"],
            "oauth": ["SECURITY_AUTH_OAUTH_ENABLED", "SECURITY_OAUTH_CALLBACK_UI"],
            "openid": ["SECURITY_AUTH_OPENID_ENABLED"],
            "kerberos": ["SECURITY_AUTH_KERBEROS_ENABLED"],
            "cas": ["SECURITY_AUTH_CAS_ENABLED"],
            "iap": ["SECURITY_AUTH_GOOGLEIAP_ENABLED"]
        }

        for provider, fields in providers.items():
            page = QWidget()
            page_layout = QVBoxLayout(page)

            if fields:  # Only create group if there are fields
                group = QGroupBox(f"{provider.upper()} Configuration")
                group_layout = QVBoxLayout()

                for field_name in fields:
                    self.add_field(group_layout, field_name)

                group.setLayout(group_layout)
                page_layout.addWidget(group)
                page_layout.addStretch()

            self.provider_stack.addWidget(page)
            self.provider_widgets[provider] = page

    def add_field(self, layout, field_name):
        """Add a configuration field to the layout"""
        field_config = self.section.fields[field_name]
        field_layout = QHBoxLayout()

        # Label
        label = QLabel(field_config.key)
        label.setToolTip(field_config.description)
        field_layout.addWidget(label)

        # Input widget
        if field_config.options:
            input_widget = QComboBox()
            input_widget.addItems(field_config.options)
            input_widget.setCurrentText(field_config.default_value)
        else:
            input_widget = QLineEdit()
            input_widget.setText(field_config.default_value)
            if field_config.is_secret:
                input_widget.setEchoMode(QLineEdit.EchoMode.Password)

        field_layout.addWidget(input_widget)

        # Help icon
        help_label = QLabel("ℹ️")
        help_label.setToolTip(field_config.description)
        field_layout.addWidget(help_label)

        layout.addLayout(field_layout)
        self.input_widgets[field_name] = input_widget

    def on_provider_changed(self, provider):
        """Handle security provider change"""
        provider_key = provider.lower().replace(" ", "")
        if provider_key in self.provider_widgets:
            self.provider_stack.setCurrentWidget(self.provider_widgets[provider_key])

            # Update ATLAS_SECURITY_PROVIDER_TYPE
            provider_type_widget = self.input_widgets.get("ATLAS_SECURITY_PROVIDER_TYPE")
            if provider_type_widget:
                if provider_key == "none":
                    provider_type_widget.setCurrentText("none")
                else:
                    provider_type_widget.setCurrentText(provider_key)

    def validate(self):
        """Validate security configuration"""
        issues = []

        provider = self.provider_selector.currentText().lower().replace(" ", "")

        for field_name, widget in self.input_widgets.items():
            field_config = self.section.fields[field_name]
            value = widget.currentText() if isinstance(widget, QComboBox) else widget.text()

            # Skip validation for disabled providers
            if field_config.provider_specific and field_config.provider_specific != provider:
                continue

            # Required field check
            if not value and not field_config.is_secret:
                issues.append(f"{field_name} is required")

            # Pattern validation
            if field_config.validation_pattern and value:
                if not re.match(field_config.validation_pattern, value):
                    issues.append(f"{field_name} has invalid format")

            # Provider-specific validations
            if provider != "none":
                enabled_field = f"SECURITY_AUTH_{provider.upper()}_ENABLED"
                if field_name == enabled_field and value.lower() == "true":
                    # Check required fields for enabled provider
                    for prov_field, prov_widget in self.input_widgets.items():
                        if self.section.fields[prov_field].provider_specific == provider:
                            prov_value = (prov_widget.currentText() if isinstance(prov_widget, QComboBox)
                                        else prov_widget.text())
                            if not prov_value and not self.section.fields[prov_field].is_secret:
                                issues.append(f"{prov_field} is required when {provider} is enabled")

        return issues

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Security Configuration")
    window.setMinimumSize(800, 600)

    security_widget = SecurityConfigWidget()
    window.setCentralWidget(security_widget)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

import sys
import os
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QScrollArea, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QComboBox, QCheckBox, QFrame, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt

@dataclass
class ConfigField:
    key: str
    default_value: str
    description: str
    options: list = None
    is_file_path: bool = False
    is_secret: bool = False
    is_boolean: bool = False
    validation_pattern: str = None
    data_type: str = None  # postgres, oracle, sqlserver, etc.

class DataSourceSection:
    """Handles data source and CDM configuration"""

    def __init__(self):
        self.section_name = "Data Source Configuration"
        self.fields = self._initialize_fields()

    def _initialize_fields(self):
        """Initialize all data source configuration fields"""
        return {
            # CDM Configuration
            "CDM_SOURCE_NAME": ConfigField(
                key="CDM_SOURCE_NAME",
                default_value="OHDSI CDM Source",
                description="Name of the CDM source"
            ),
            "CDM_VERSION": ConfigField(
                key="CDM_VERSION",
                default_value="5.3",
                description="CDM version",
                options=["5.3", "5.4"]
            ),
            "CDM_CONNECTIONDETAILS_DBMS": ConfigField(
                key="CDM_CONNECTIONDETAILS_DBMS",
                default_value="postgresql",
                description="Database management system",
                options=["postgresql", "oracle", "sqlserver", "redshift", "snowflake"],
                data_type="connection"
            ),
            "CDM_CONNECTIONDETAILS_SERVER": ConfigField(
                key="CDM_CONNECTIONDETAILS_SERVER",
                default_value="localhost/postgres",
                description="Database server address"
            ),
            "CDM_CONNECTIONDETAILS_PORT": ConfigField(
                key="CDM_CONNECTIONDETAILS_PORT",
                default_value="5432",
                description="Database port",
                validation_pattern=r"^\d+$"
            ),
            "CDM_CONNECTIONDETAILS_USER": ConfigField(
                key="CDM_CONNECTIONDETAILS_USER",
                default_value="postgres",
                description="Database username"
            ),
            "CDM_CONNECTIONDETAILS_PASSWORD_FILE": ConfigField(
                key="CDM_CONNECTIONDETAILS_PASSWORD_FILE",
                default_value="./secrets/cdm/CDM_PASSWORD",
                description="Path to database password file",
                is_file_path=True,
                is_secret=True
            ),

            # Schema Configuration
            "CDM_DATABASE_SCHEMA": ConfigField(
                key="CDM_DATABASE_SCHEMA",
                default_value="cdm",
                description="CDM schema name"
            ),
            "RESULTS_DATABASE_SCHEMA": ConfigField(
                key="RESULTS_DATABASE_SCHEMA",
                default_value="results",
                description="Results schema name"
            ),
            "TEMP_DATABASE_SCHEMA": ConfigField(
                key="TEMP_DATABASE_SCHEMA",
                default_value="temp",
                description="Temporary schema name"
            ),
            "VOCAB_DATABASE_SCHEMA": ConfigField(
                key="VOCAB_DATABASE_SCHEMA",
                default_value="vocab",
                description="Vocabulary schema name"
            ),

            # Vocabulary Configuration
            "VOCAB_PG_HOST": ConfigField(
                key="VOCAB_PG_HOST",
                default_value="localhost",
                description="Vocabulary database host"
            ),
            "VOCAB_PG_DATABASE": ConfigField(
                key="VOCAB_PG_DATABASE",
                default_value="postgres",
                description="Vocabulary database name"
            ),
            "VOCAB_PG_SCHEMA": ConfigField(
                key="VOCAB_PG_SCHEMA",
                default_value="vocab",
                description="Vocabulary schema name"
            ),
            "VOCAB_PG_USER": ConfigField(
                key="VOCAB_PG_USER",
                default_value="postgres",
                description="Vocabulary database username"
            ),
            "VOCAB_PG_PASSWORD_FILE": ConfigField(
                key="VOCAB_PG_PASSWORD_FILE",
                default_value="./secrets/vocab/VOCAB_PASSWORD",
                description="Path to vocabulary database password file",
                is_file_path=True,
                is_secret=True
            ),
            "VOCAB_PG_FILES_PATH": ConfigField(
                key="VOCAB_PG_FILES_PATH",
                default_value="./vocab/files",
                description="Path to vocabulary files",
                is_file_path=True
            ),

            # UMLS Configuration
            "UMLS_API_KEY_FILE": ConfigField(
                key="UMLS_API_KEY_FILE",
                default_value="./secrets/vocab/UMLS_API_KEY",
                description="Path to UMLS API key file",
                is_file_path=True,
                is_secret=True
            )
        }

class DataSourceConfigWidget(QWidget):
    """Widget for data source configuration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.section = DataSourceSection()
        self.input_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI for data source configuration"""
        layout = QVBoxLayout(self)

        # CDM Connection Settings
        self.add_cdm_connection_group(layout)

        # Schema Configuration
        self.add_schema_config_group(layout)

        # Vocabulary Configuration
        self.add_vocab_config_group(layout)

        # Connection Test Button
        test_button = QPushButton("Test Connections")
        test_button.clicked.connect(self.test_connections)
        layout.addWidget(test_button)

    def add_cdm_connection_group(self, parent_layout):
        """Add CDM connection configuration group"""
        group = QGroupBox("CDM Connection Settings")
        layout = QVBoxLayout()

        fields = [
            "CDM_SOURCE_NAME",
            "CDM_VERSION",
            "CDM_CONNECTIONDETAILS_DBMS",
            "CDM_CONNECTIONDETAILS_SERVER",
            "CDM_CONNECTIONDETAILS_PORT",
            "CDM_CONNECTIONDETAILS_USER",
            "CDM_CONNECTIONDETAILS_PASSWORD_FILE"
        ]

        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_schema_config_group(self, parent_layout):
        """Add schema configuration group"""
        group = QGroupBox("Schema Configuration")
        layout = QVBoxLayout()

        fields = [
            "CDM_DATABASE_SCHEMA",
            "RESULTS_DATABASE_SCHEMA",
            "TEMP_DATABASE_SCHEMA",
            "VOCAB_DATABASE_SCHEMA"
        ]

        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_vocab_config_group(self, parent_layout):
        """Add vocabulary configuration group"""
        group = QGroupBox("Vocabulary Configuration")
        layout = QVBoxLayout()

        fields = [
            "VOCAB_PG_HOST",
            "VOCAB_PG_DATABASE",
            "VOCAB_PG_SCHEMA",
            "VOCAB_PG_USER",
            "VOCAB_PG_PASSWORD_FILE",
            "VOCAB_PG_FILES_PATH",
            "UMLS_API_KEY_FILE"
        ]

        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_field(self, layout, field_name):
        """Add a configuration field to the layout"""
        field_config = self.section.fields[field_name]
        field_layout = QHBoxLayout()

        # Label
        label = QLabel(field_name)
        label.setToolTip(field_config.description)
        field_layout.addWidget(label)

        # Input widget
        if field_config.options:
            input_widget = QComboBox()
            input_widget.addItems(field_config.options)
            input_widget.setCurrentText(field_config.default_value)

            # Special handling for DBMS selection
            if field_name == "CDM_CONNECTIONDETAILS_DBMS":
                input_widget.currentTextChanged.connect(self.on_dbms_changed)
        else:
            input_widget = QLineEdit()
            input_widget.setText(field_config.default_value)
            if field_config.is_secret:
                input_widget.setEchoMode(QLineEdit.EchoMode.Password)

        field_layout.addWidget(input_widget)

        # Add file browser for file paths
        if field_config.is_file_path:
            browse_button = QPushButton("Browse...")
            browse_button.clicked.connect(
                lambda checked, w=input_widget: self.browse_file_path(w)
            )
            field_layout.addWidget(browse_button)

        # Help icon
        help_label = QLabel("ℹ️")
        help_label.setToolTip(field_config.description)
        field_layout.addWidget(help_label)

        layout.addLayout(field_layout)
        self.input_widgets[field_name] = input_widget

    def browse_file_path(self, input_widget):
        """Handle file/directory browsing"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Directory", os.path.expanduser("~")
        )
        if path:
            input_widget.setText(path)

    def on_dbms_changed(self, dbms):
        """Handle database management system change"""
        # Update port based on selected DBMS
        port_widget = self.input_widgets.get("CDM_CONNECTIONDETAILS_PORT")
        if port_widget:
            default_ports = {
                "postgresql": "5432",
                "oracle": "1521",
                "sqlserver": "1433",
                "redshift": "5439",
                "snowflake": "443"
            }
            port_widget.setText(default_ports.get(dbms, ""))

    def test_connections(self):
        """Test database connections"""
        # In a real implementation, this would attempt to connect to the databases
        # For now, we'll just validate the configuration
        issues = self.validate()

        if issues:
            QMessageBox.warning(
                self,
                "Connection Test Failed",
                "The following issues were found:\n\n" + "\n".join(issues)
            )
        else:
            QMessageBox.information(
                self,
                "Connection Test Successful",
                "All connection parameters appear valid."
            )

    def validate(self) -> List[str]:
        """Validate data source configuration"""
        issues = []

        for field_name, widget in self.input_widgets.items():
            field_config = self.section.fields[field_name]
            value = widget.currentText() if isinstance(widget, QComboBox) else widget.text()

            # Required field check
            if not value and not field_config.is_secret:
                issues.append(f"{field_name} is required")

            # Pattern validation
            if field_config.validation_pattern and value:
                if not re.match(field_config.validation_pattern, value):
                    issues.append(f"{field_name} has invalid format")

            # File path validation
            if field_config.is_file_path and value:
                parent_dir = os.path.dirname(value)
                if not os.path.exists(parent_dir):
                    issues.append(f"Directory for {field_name} does not exist: {parent_dir}")

            # Port number validation
            if field_name == "CDM_CONNECTIONDETAILS_PORT":
                try:
                    port = int(value)
                    if port < 1 or port > 65535:
                        issues.append("Port number must be between 1 and 65535")
                except ValueError:
                    issues.append("Port must be a number")

        return issues

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Data Source Configuration")
    window.setMinimumSize(800, 600)

    datasource_widget = DataSourceConfigWidget()
    window.setCentralWidget(datasource_widget)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

import sys
import os
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QScrollArea, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QComboBox, QCheckBox, QFrame, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt

@dataclass
class ConfigField:
    key: str
    default_value: str
    description: str
    options: list = None
    is_file_path: bool = False
    is_secret: bool = False
    is_boolean: bool = False
    validation_pattern: str = None
    build_type: str = None  # atlas, webapi, etc.

class BuildSection:
    """Handles build and deployment configuration"""

    def __init__(self):
        self.section_name = "Build and Deployment Configuration"
        self.fields = self._initialize_fields()

    def _initialize_fields(self):
        """Initialize all build configuration fields"""
        return {
            # Atlas Build Configuration
            "ATLAS_GITHUB_URL": ConfigField(
                key="ATLAS_GITHUB_URL",
                default_value="https://github.com/OHDSI/Atlas.git#master",
                description="Atlas GitHub repository URL and branch/tag",
                validation_pattern=r"^https:\/\/github\.com\/[\w-]+\/[\w-]+(\.git)?(#[\w\.-]+)?$",
                build_type="atlas"
            ),
            "ATLAS_BUILD_FROM_GIT": ConfigField(
                key="ATLAS_BUILD_FROM_GIT",
                default_value="false",
                description="Build Atlas from Git instead of using Docker Hub image",
                options=["true", "false"],
                is_boolean=True,
                build_type="atlas"
            ),

            # WebAPI Build Configuration
            "WEBAPI_GITHUB_URL": ConfigField(
                key="WEBAPI_GITHUB_URL",
                default_value="https://github.com/OHDSI/WebAPI.git#master",
                description="WebAPI GitHub repository URL and branch/tag",
                validation_pattern=r"^https:\/\/github\.com\/[\w-]+\/[\w-]+(\.git)?(#[\w\.-]+)?$",
                build_type="webapi"
            ),
            "WEBAPI_MAVEN_PROFILE": ConfigField(
                key="WEBAPI_MAVEN_PROFILE",
                default_value="webapi-docker",
                description="Maven profile for WebAPI build",
                options=["webapi-docker", "webapi-docker,webapi-solr"],
                build_type="webapi"
            ),

            # Docker Configuration
            "DOCKER_ARCH": ConfigField(
                key="DOCKER_ARCH",
                default_value="linux/amd64",
                description="Docker architecture",
                options=["linux/amd64", "linux/arm64"],
                build_type="docker"
            ),
            "DOCKER_COMPOSE_VERSION": ConfigField(
                key="DOCKER_COMPOSE_VERSION",
                default_value="3.8",
                description="Docker Compose version",
                options=["3.7", "3.8", "3.9"],
                build_type="docker"
            ),

            # SOLR Configuration
            "SOLR_VOCAB_ENDPOINT": ConfigField(
                key="SOLR_VOCAB_ENDPOINT",
                default_value="http://broadsea-solr-vocab:8983/solr",
                description="SOLR vocabulary endpoint",
                validation_pattern=r"^https?:\/\/[\w\-\.]+:\d+\/.*$",
                build_type="solr"
            ),
            "SOLR_VOCAB_VERSION": ConfigField(
                key="SOLR_VOCAB_VERSION",
                default_value="v5.0_23-JAN-23",
                description="SOLR vocabulary version",
                build_type="solr"
            ),

            # Build Environment
            "BUILD_ENV": ConfigField(
                key="BUILD_ENV",
                default_value="production",
                description="Build environment",
                options=["development", "staging", "production"],
                build_type="environment"
            ),
            "ENABLE_DEBUG": ConfigField(
                key="ENABLE_DEBUG",
                default_value="false",
                description="Enable debug mode",
                options=["true", "false"],
                is_boolean=True,
                build_type="environment"
            )
        }

class BuildConfigWidget(QWidget):
    """Widget for build configuration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.section = BuildSection()
        self.input_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI for build configuration"""
        layout = QVBoxLayout(self)

        # Atlas Build Settings
        self.add_atlas_build_group(layout)

        # WebAPI Build Settings
        self.add_webapi_build_group(layout)

        # Docker Settings
        self.add_docker_config_group(layout)

        # SOLR Settings
        self.add_solr_config_group(layout)

        # Environment Settings
        self.add_environment_config_group(layout)

        # Build Actions
        self.add_build_actions(layout)

    def add_atlas_build_group(self, parent_layout):
        """Add Atlas build configuration group"""
        group = QGroupBox("Atlas Build Configuration")
        layout = QVBoxLayout()

        fields = ["ATLAS_GITHUB_URL", "ATLAS_BUILD_FROM_GIT"]
        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_webapi_build_group(self, parent_layout):
        """Add WebAPI build configuration group"""
        group = QGroupBox("WebAPI Build Configuration")
        layout = QVBoxLayout()

        fields = ["WEBAPI_GITHUB_URL", "WEBAPI_MAVEN_PROFILE"]
        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_docker_config_group(self, parent_layout):
        """Add Docker configuration group"""
        group = QGroupBox("Docker Configuration")
        layout = QVBoxLayout()

        fields = ["DOCKER_ARCH", "DOCKER_COMPOSE_VERSION"]
        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_solr_config_group(self, parent_layout):
        """Add SOLR configuration group"""
        group = QGroupBox("SOLR Configuration")
        layout = QVBoxLayout()

        fields = ["SOLR_VOCAB_ENDPOINT", "SOLR_VOCAB_VERSION"]
        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_environment_config_group(self, parent_layout):
        """Add environment configuration group"""
        group = QGroupBox("Environment Configuration")
        layout = QVBoxLayout()

        fields = ["BUILD_ENV", "ENABLE_DEBUG"]
        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_build_actions(self, parent_layout):
        """Add build action buttons"""
        actions_layout = QHBoxLayout()

        validate_button = QPushButton("Validate Configuration")
        validate_button.clicked.connect(self.validate_config)
        actions_layout.addWidget(validate_button)

        generate_button = QPushButton("Generate Docker Compose")
        generate_button.clicked.connect(self.generate_docker_compose)
        actions_layout.addWidget(generate_button)

        parent_layout.addLayout(actions_layout)

    def add_field(self, layout, field_name):
        """Add a configuration field to the layout"""
        field_config = self.section.fields[field_name]
        field_layout = QHBoxLayout()

        # Label
        label = QLabel(field_name)
        label.setToolTip(field_config.description)
        field_layout.addWidget(label)

        # Input widget
        if field_config.options:
            input_widget = QComboBox()
            input_widget.addItems(field_config.options)
            input_widget.setCurrentText(field_config.default_value)
        else:
            input_widget = QLineEdit()
            input_widget.setText(field_config.default_value)

        field_layout.addWidget(input_widget)

        # Help icon
        help_label = QLabel("ℹ️")
        help_label.setToolTip(field_config.description)
        field_layout.addWidget(help_label)

        layout.addLayout(field_layout)
        self.input_widgets[field_name] = input_widget

    def validate_config(self):
        """Validate build configuration"""
        issues = []

        for field_name, widget in self.input_widgets.items():
            field_config = self.section.fields[field_name]
            value = widget.currentText() if isinstance(widget, QComboBox) else widget.text()

            # Required field check
            if not value:
                issues.append(f"{field_name} is required")

            # Pattern validation
            if field_config.validation_pattern and value:
                if not re.match(field_config.validation_pattern, value):
                    issues.append(f"{field_name} has invalid format")

            # Build-specific validations
            if field_config.build_type == "atlas":
                if "ATLAS_BUILD_FROM_GIT" in field_name and value.lower() == "true":
                    github_url = self.input_widgets["ATLAS_GITHUB_URL"].text()
                    if not github_url or not github_url.startswith("https://github.com/"):
                        issues.append("Invalid Atlas GitHub URL for Git build")

            elif field_config.build_type == "webapi":
                if "WEBAPI_MAVEN_PROFILE" in field_name and "solr" in value.lower():
                    solr_endpoint = self.input_widgets["SOLR_VOCAB_ENDPOINT"].text()
                    if not solr_endpoint:
                        issues.append("SOLR endpoint is required when using SOLR profile")

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
                "All build configuration values are valid!"
            )

    def generate_docker_compose(self):
        """Generate Docker Compose configuration"""
        # This would generate the docker-compose.yml file based on the configuration
        try:
            if self.validate_config():
                QMessageBox.information(
                    self,
                    "Docker Compose Generation",
                    "Docker Compose configuration would be generated here.\n"
                    "This is a placeholder for the actual implementation."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Failed to generate Docker Compose configuration: {str(e)}"
            )

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Build Configuration")
    window.setMinimumSize(800, 600)

    build_widget = BuildConfigWidget()
    window.setCentralWidget(build_widget)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

import sys
import os
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QScrollArea, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QComboBox, QCheckBox, QFrame, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox
)
from PyQt6.QtCore import Qt

@dataclass
class ConfigField:
    key: str
    default_value: str
    description: str
    options: list = None
    is_file_path: bool = False
    is_secret: bool = False
    is_boolean: bool = False
    validation_pattern: str = None
    category: str = None  # logging, monitoring, analytics
    is_numeric: bool = False
    min_value: int = None
    max_value: int = None

class MonitoringSection:
    """Handles monitoring, logging, and analytics configuration"""

    def __init__(self):
        self.section_name = "Monitoring and Logging Configuration"
        self.fields = self._initialize_fields()

    def _initialize_fields(self):
        """Initialize all monitoring configuration fields"""
        return {
            # Logging Configuration
            "LOG_LEVEL": ConfigField(
                key="LOG_LEVEL",
                default_value="INFO",
                description="Application-wide logging level",
                options=["DEBUG", "INFO", "WARN", "ERROR"],
                category="logging"
            ),
            "LOG_FORMAT": ConfigField(
                key="LOG_FORMAT",
                default_value="json",
                description="Log output format",
                options=["json", "text", "csv"],
                category="logging"
            ),
            "LOG_PATH": ConfigField(
                key="LOG_PATH",
                default_value="./logs",
                description="Directory for log files",
                is_file_path=True,
                category="logging"
            ),
            "LOG_RETENTION_DAYS": ConfigField(
                key="LOG_RETENTION_DAYS",
                default_value="30",
                description="Number of days to retain logs",
                is_numeric=True,
                min_value=1,
                max_value=365,
                category="logging"
            ),
            "LOG_MAX_SIZE": ConfigField(
                key="LOG_MAX_SIZE",
                default_value="100",
                description="Maximum log file size in MB",
                is_numeric=True,
                min_value=1,
                max_value=1000,
                category="logging"
            ),

            # Monitoring Configuration
            "ENABLE_METRICS": ConfigField(
                key="ENABLE_METRICS",
                default_value="true",
                description="Enable Prometheus metrics",
                options=["true", "false"],
                is_boolean=True,
                category="monitoring"
            ),
            "METRICS_PORT": ConfigField(
                key="METRICS_PORT",
                default_value="9090",
                description="Prometheus metrics port",
                validation_pattern=r"^\d+$",
                is_numeric=True,
                min_value=1024,
                max_value=65535,
                category="monitoring"
            ),
            "ENABLE_HEALTH_CHECK": ConfigField(
                key="ENABLE_HEALTH_CHECK",
                default_value="true",
                description="Enable health check endpoint",
                options=["true", "false"],
                is_boolean=True,
                category="monitoring"
            ),
            "HEALTH_CHECK_PATH": ConfigField(
                key="HEALTH_CHECK_PATH",
                default_value="/health",
                description="Health check endpoint path",
                category="monitoring"
            ),

            # Performance Monitoring
            "ENABLE_TRACING": ConfigField(
                key="ENABLE_TRACING",
                default_value="false",
                description="Enable distributed tracing",
                options=["true", "false"],
                is_boolean=True,
                category="monitoring"
            ),
            "TRACING_SAMPLE_RATE": ConfigField(
                key="TRACING_SAMPLE_RATE",
                default_value="0.1",
                description="Tracing sample rate (0.0 to 1.0)",
                validation_pattern=r"^0(\.\d+)?|1(\.0)?$",
                category="monitoring"
            ),

            # Analytics Configuration
            "ENABLE_USAGE_STATS": ConfigField(
                key="ENABLE_USAGE_STATS",
                default_value="true",
                description="Enable usage statistics collection",
                options=["true", "false"],
                is_boolean=True,
                category="analytics"
            ),
            "ANALYTICS_DB_PATH": ConfigField(
                key="ANALYTICS_DB_PATH",
                default_value="./analytics/db",
                description="Analytics database path",
                is_file_path=True,
                category="analytics"
            ),
            "ANALYTICS_RETENTION_MONTHS": ConfigField(
                key="ANALYTICS_RETENTION_MONTHS",
                default_value="12",
                description="Months to retain analytics data",
                is_numeric=True,
                min_value=1,
                max_value=60,
                category="analytics"
            )
        }

class MonitoringConfigWidget(QWidget):
    """Widget for monitoring configuration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.section = MonitoringSection()
        self.input_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI for monitoring configuration"""
        layout = QVBoxLayout(self)

        # Logging Configuration
        self.add_logging_group(layout)

        # Monitoring Configuration
        self.add_monitoring_group(layout)

        # Analytics Configuration
        self.add_analytics_group(layout)

        # Actions
        self.add_actions(layout)

    def add_logging_group(self, parent_layout):
        """Add logging configuration group"""
        group = QGroupBox("Logging Configuration")
        layout = QVBoxLayout()

        fields = [
            "LOG_LEVEL",
            "LOG_FORMAT",
            "LOG_PATH",
            "LOG_RETENTION_DAYS",
            "LOG_MAX_SIZE"
        ]

        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_monitoring_group(self, parent_layout):
        """Add monitoring configuration group"""
        group = QGroupBox("Monitoring Configuration")
        layout = QVBoxLayout()

        fields = [
            "ENABLE_METRICS",
            "METRICS_PORT",
            "ENABLE_HEALTH_CHECK",
            "HEALTH_CHECK_PATH",
            "ENABLE_TRACING",
            "TRACING_SAMPLE_RATE"
        ]

        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_analytics_group(self, parent_layout):
        """Add analytics configuration group"""
        group = QGroupBox("Analytics Configuration")
        layout = QVBoxLayout()

        fields = [
            "ENABLE_USAGE_STATS",
            "ANALYTICS_DB_PATH",
            "ANALYTICS_RETENTION_MONTHS"
        ]

        for field_name in fields:
            self.add_field(layout, field_name)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_field(self, layout, field_name):
        """Add a configuration field to the layout"""
        field_config = self.section.fields[field_name]
        field_layout = QHBoxLayout()

        # Label
        label = QLabel(field_name)
        label.setToolTip(field_config.description)
        field_layout.addWidget(label)

        # Input widget
        if field_config.is_numeric:
            input_widget = QSpinBox()
            input_widget.setMinimum(field_config.min_value or 0)
            input_widget.setMaximum(field_config.max_value or 99999)
            input_widget.setValue(int(field_config.default_value))
        elif field_config.options:
            input_widget = QComboBox()
            input_widget.addItems(field_config.options)
            input_widget.setCurrentText(field_config.default_value)
        else:
            input_widget = QLineEdit()
            input_widget.setText(field_config.default_value)

        # Add file browser for file paths
        if field_config.is_file_path:
            browse_button = QPushButton("Browse...")
            browse_button.clicked.connect(
                lambda checked, w=input_widget: self.browse_file_path(w)
            )
            field_layout.addWidget(browse_button)

        field_layout.addWidget(input_widget)

        # Help icon
        help_label = QLabel("ℹ️")
        help_label.setToolTip(field_config.description)
        field_layout.addWidget(help_label)

        layout.addLayout(field_layout)
        self.input_widgets[field_name] = input_widget

    def browse_file_path(self, input_widget):
        """Handle file/directory browsing"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Directory", os.path.expanduser("~")
        )
        if path:
            input_widget.setText(path)

    def add_actions(self, parent_layout):
        """Add action buttons"""
        actions_layout = QHBoxLayout()

        validate_button = QPushButton("Validate Configuration")
        validate_button.clicked.connect(self.validate_config)
        actions_layout.addWidget(validate_button)

        test_button = QPushButton("Test Logging")
        test_button.clicked.connect(self.test_logging)
        actions_layout.addWidget(test_button)

        parent_layout.addLayout(actions_layout)

    def validate_config(self):
        """Validate monitoring configuration"""
        issues = []

        for field_name, widget in self.input_widgets.items():
            field_config = self.section.fields[field_name]

            if isinstance(widget, QSpinBox):
                value = str(widget.value())
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            else:
                value = widget.text()

            # Required field check
            if not value:
                issues.append(f"{field_name} is required")

            # Pattern validation
            if field_config.validation_pattern and value:
                if not re.match(field_config.validation_pattern, value):
                    issues.append(f"{field_name} has invalid format")

            # File path validation
            if field_config.is_file_path and value:
                parent_dir = os.path.dirname(value)
                if not os.path.exists(parent_dir):
                    issues.append(f"Directory for {field_name} does not exist: {parent_dir}")

            # Numeric validation
            if field_config.is_numeric and value:
                try:
                    num_value = float(value)
                    if field_config.min_value is not None and num_value < field_config.min_value:
                        issues.append(f"{field_name} must be at least {field_config.min_value}")
                    if field_config.max_value is not None and num_value > field_config.max_value:
                        issues.append(f"{field_name} must be no more than {field_config.max_value}")
                except ValueError:
                    issues.append(f"{field_name} must be a number")

            # Special validations
            if field_name == "METRICS_PORT":
                port = int(value)
                if port < 1024 or port > 65535:
                    issues.append("Metrics port must be between 1024 and 65535")

            elif field_name == "TRACING_SAMPLE_RATE":
                try:
                    rate = float(value)
                    if rate < 0.0 or rate > 1.0:
                        issues.append("Tracing sample rate must be between 0.0 and 1.0")
                except ValueError:
                    issues.append("Invalid tracing sample rate")

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
                "All monitoring configuration values are valid!"
            )

    def test_logging(self):
        """Test logging configuration"""
        log_path = self.input_widgets["LOG_PATH"].text()

        try:
            # Create log directory if it doesn't exist
            os.makedirs(log_path, exist_ok=True)

            # Try to write a test log entry
            test_log_path = os.path.join(log_path, "test.log")
            with open(test_log_path, "w") as f:
                f.write("Test log entry\n")

            QMessageBox.information(
                self,
                "Logging Test",
                f"Successfully wrote test log to:\n{test_log_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Logging Test Failed",
                f"Failed to write test log: {str(e)}"
            )

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Monitoring Configuration")
    window.setMinimumSize(800, 600)

    monitoring_widget = MonitoringConfigWidget()
    window.setCentralWidget(monitoring_widget)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

