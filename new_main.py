import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QWizard, QWizardPage, QLineEdit,
    QComboBox, QCheckBox, QTextEdit, QMessageBox, QFileDialog,
    QGroupBox, QScrollArea, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

@dataclass
class ConfigField:
    name: str
    description: str
    default_value: str = ""
    required: bool = True
    depends_on: Optional[Dict[str, str]] = None
    validation_func: Optional[callable] = None
    options: Optional[List[str]] = None
    field_type: str = "text"  # text, password, combo, checkbox, file
    help_text: str = ""
    placeholder: str = ""
    section: str = ""
    group: str = ""

class ConfigSection:
    def __init__(self, name: str, title: str, description: str):
        self.name = name
        self.title = title
        self.description = description
        self.fields: List[ConfigField] = []
        self.groups: Dict[str, str] = {}

    def add_field(self, field: ConfigField):
        field.section = self.name
        self.fields.append(field)

    def add_group(self, name: str, title: str):
        self.groups[name] = title

class ConfigWizardPage(QWizardPage):
    def __init__(self, section: ConfigSection, parent=None):
        super().__init__(parent)
        self.section = section
        self.fields: Dict[str, QWidget] = {}
        self.setup_ui()

    def setup_ui(self):
        self.setTitle(self.section.title)
        self.setSubTitle(self.section.description)

        # Create main layout
        layout = QVBoxLayout(self)

        # Dictionary to track dependencies
        self.dependency_map = {}
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Group fields
        current_group = None
        group_layout = None

        for field in self.section.fields:
            # Create new group if needed
            if field.group != current_group:
                current_group = field.group
                if current_group in self.section.groups:
                    group_box = QGroupBox(self.section.groups[current_group])
                    group_layout = QVBoxLayout()
                    group_box.setLayout(group_layout)
                    content_layout.addWidget(group_box)
                else:
                    group_layout = content_layout

            # Create field widget
            field_widget = self.create_field_widget(field)
            if field_widget:
                field_container = QWidget()
                field_layout = QVBoxLayout(field_container)
                field_layout.setContentsMargins(0, 0, 0, 10)

                # Add label with required indicator
                label_text = field.name
                if field.required:
                    label_text += " *"
                label = QLabel(label_text)
                label.setFont(QFont("Arial", weight=QFont.Weight.Bold))
                field_layout.addWidget(label)

                # Add description
                if field.description:
                    desc = QLabel(field.description)
                    desc.setWordWrap(True)
                    desc.setStyleSheet("color: #666;")
                    field_layout.addWidget(desc)

                # Add the actual field widget
                field_layout.addWidget(field_widget)

                # Add help text if present
                if field.help_text:
                    help_label = QLabel(field.help_text)
                    help_label.setWordWrap(True)
                    help_label.setStyleSheet("color: #666; font-style: italic;")
                    field_layout.addWidget(help_label)

                group_layout.addWidget(field_container)
                self.fields[field.name] = field_widget

                # Setup field dependencies
                if field.depends_on:
                    for dep_field, dep_value in field.depends_on.items():
                        if dep_field not in self.dependency_map:
                            self.dependency_map[dep_field] = []
                        self.dependency_map[dep_field].append({
                            'target_field': field.name,
                            'required_value': dep_value,
                            'container': field_container
                        })
                        # Initially hide if dependency not met
                        if dep_field in self.fields:
                            self.update_field_visibility(dep_field)

        # Connect dependency signals
        for field_name, field_widget in self.fields.items():
            if field_name in self.dependency_map:
                if isinstance(field_widget, QCheckBox):
                    field_widget.stateChanged.connect(
                        lambda state, name=field_name: self.update_field_visibility(name)
                    )
                elif isinstance(field_widget, QComboBox):
                    field_widget.currentTextChanged.connect(
                        lambda text, name=field_name: self.update_field_visibility(name)
                    )
                elif isinstance(field_widget, QLineEdit):
                    field_widget.textChanged.connect(
                        lambda text, name=field_name: self.update_field_visibility(name)
                    )

        # Add vertical spacer at the bottom
        content_layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def create_field_widget(self, field: ConfigField) -> QWidget:
        if field.field_type == "text":
            widget = QLineEdit()
            widget.setText(field.default_value)
            widget.setPlaceholderText(field.placeholder)
            return widget
        elif field.field_type == "password":
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            widget.setText(field.default_value)
            widget.setPlaceholderText(field.placeholder)
            return widget
        elif field.field_type == "combo" and field.options:
            widget = QComboBox()
            widget.addItems(field.options)
            if field.default_value in field.options:
                widget.setCurrentText(field.default_value)
            return widget
        elif field.field_type == "checkbox":
            widget = QCheckBox()
            widget.setChecked(field.default_value.lower() == "true")
            return widget
        elif field.field_type == "file":
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            line_edit = QLineEdit()
            line_edit.setText(field.default_value)
            line_edit.setPlaceholderText(field.placeholder)
            
            browse_btn = QPushButton("Browse...")
            browse_btn.clicked.connect(
                lambda: self.browse_file(line_edit, field.name)
            )
            
            layout.addWidget(line_edit)
            layout.addWidget(browse_btn)
            
            self.fields[field.name] = line_edit
            return container
        return None

    def browse_file(self, line_edit: QLineEdit, field_name: str):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {field_name}",
            "",
            "All Files (*.*)"
        )
        if filename:
            line_edit.setText(filename)

    def update_field_visibility(self, field_name: str):
        """Update visibility of dependent fields"""
        if field_name not in self.dependency_map:
            return

        field_widget = self.fields[field_name]
        current_value = ""
        
        if isinstance(field_widget, QCheckBox):
            current_value = str(field_widget.isChecked()).lower()
        elif isinstance(field_widget, QComboBox):
            current_value = field_widget.currentText()
        elif isinstance(field_widget, QLineEdit):
            current_value = field_widget.text()
        elif isinstance(field_widget, QTextEdit):
            current_value = field_widget.toPlainText()

        for dependency in self.dependency_map[field_name]:
            show = current_value == dependency['required_value']
            dependency['container'].setVisible(show)
            # Clear value when hidden
            if not show and dependency['target_field'] in self.fields:
                target_widget = self.fields[dependency['target_field']]
                if isinstance(target_widget, QLineEdit):
                    target_widget.clear()
                elif isinstance(target_widget, QComboBox):
                    target_widget.setCurrentIndex(0)
                elif isinstance(target_widget, QCheckBox):
                    target_widget.setChecked(False)
                elif isinstance(target_widget, QTextEdit):
                    target_widget.clear()

    def get_field_value(self, field_name: str) -> str:
        widget = self.fields.get(field_name)
        if not widget:
            return ""
            
        # Skip hidden fields
        if not widget.isVisible():
            return ""
            
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QCheckBox):
            return str(widget.isChecked()).lower()
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText()
        return ""

class ConfigWizard(QWizard):
    def __init__(self, sections: List[ConfigSection], parent=None):
        super().__init__(parent)
        self.sections = sections
        self.pages: List[ConfigWizardPage] = []
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Broadsea Configuration Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        
        # Add pages for each section
        for section in self.sections:
            page = ConfigWizardPage(section)
            self.addPage(page)
            self.pages.append(page)

        # Set window properties
        self.setMinimumSize(800, 600)
        
        # Connect signals
        self.finished.connect(self.on_finish)

    def get_config(self) -> Dict[str, Dict[str, str]]:
        config = {}
        for page in self.pages:
            section_config = {}
            for field in page.section.fields:
                value = page.get_field_value(field.name)
                if value or field.required:
                    section_config[field.name] = value
            config[page.section.name] = section_config
        return config

    def validate_field(self, field: ConfigField, value: str) -> Optional[str]:
        """Validate a field value"""
        if field.required and not value:
            return f"{field.name} is required"
            
        if field.validation_func:
            try:
                if not field.validation_func(value):
                    return f"{field.name} validation failed"
            except Exception as e:
                return f"{field.name} validation error: {str(e)}"
                
        return None

    def validate_page(self, page: ConfigWizardPage) -> List[str]:
        """Validate all fields on a page"""
        issues = []
        for field in page.section.fields:
            value = page.get_field_value(field.name)
            if error := self.validate_field(field, value):
                issues.append(error)
        return issues

    def validate_all(self) -> List[str]:
        """Validate all pages"""
        issues = []
        for page in self.pages:
            page_issues = self.validate_page(page)
            if page_issues:
                issues.extend([f"{page.section.title}: {issue}" for issue in page_issues])
        return issues

    def on_finish(self):
        if self.result() == QWizard.DialogCode.Accepted:
            # Validate all fields
            if issues := self.validate_all():
                QMessageBox.warning(
                    self,
                    "Validation Issues",
                    "Please fix the following issues:\n\n" + "\n".join(issues)
                )
                return

            try:
                config = self.get_config()
                self.save_config(config)
                QMessageBox.information(
                    self,
                    "Success",
                    "Configuration saved successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save configuration: {str(e)}"
                )

    def save_config(self, config: Dict[str, Dict[str, str]]):
        try:
            with open('.env', 'w') as f:
                for section_name, section_config in config.items():
                    f.write(f"{'#' * 92}\n")
                    f.write(f"# Section: {section_name}\n")
                    f.write(f"{'#' * 92}\n\n")

                    for key, value in section_config.items():
                        f.write(f"{key}={value}\n")
                    f.write("\n")
        except Exception as e:
            raise Exception(f"Failed to save configuration: {str(e)}")

def create_sections() -> List[ConfigSection]:
    sections = []

    # Host Configuration
    host = ConfigSection(
        "Host",
        "Broadsea Host Configuration",
        "Configure basic host settings for Broadsea"
    )
    host.add_group("basic", "Basic Settings")
    host.add_field(ConfigField(
        "DOCKER_ARCH",
        "Docker architecture to use",
        default_value="linux/amd64",
        options=["linux/amd64", "linux/arm64"],
        field_type="combo",
        help_text="Use linux/arm64 for Mac Silicon, otherwise keep as linux/amd64",
        group="basic"
    ))
    host.add_field(ConfigField(
        "BROADSEA_HOST",
        "Host URL without protocol",
        default_value="127.0.0.1",
        help_text="Change to your host URL (without the http part)",
        group="basic"
    ))
    host.add_field(ConfigField(
        "HTTP_TYPE",
        "HTTP protocol type",
        default_value="http",
        options=["http", "https"],
        field_type="combo",
        help_text="If using https, you need to add the crt and key files to the ./certs folder",
        group="basic"
    ))
    sections.append(host)

    # Atlas Configuration
    atlas = ConfigSection(
        "Atlas",
        "Atlas Configuration",
        "Configure OHDSI Atlas settings"
    )
    atlas.add_group("basic", "Basic Settings")
    atlas.add_group("auth", "Authentication")
    atlas.add_group("features", "Feature Flags")
    
    # Basic Settings
    atlas.add_field(ConfigField(
        "ATLAS_VERSION",
        "Atlas Version",
        default_value="2.12.0",
        group="basic"
    ))
    atlas.add_field(ConfigField(
        "ATLAS_PORT",
        "Atlas Port",
        default_value="8080",
        validation_func=lambda x: x.isdigit() and 0 <= int(x) <= 65535,
        group="basic"
    ))
    
    # Authentication
    atlas.add_field(ConfigField(
        "ATLAS_USER_AUTH_ENABLED",
        "Enable User Authentication",
        default_value="false",
        field_type="checkbox",
        help_text="Enable if using security, but ensure you fill out the WebAPI/Atlas security sections",
        group="auth"
    ))
    
    # Feature Flags
    atlas.add_field(ConfigField(
        "ATLAS_COHORT_COMPARISON_RESULTS_ENABLED",
        "Enable Cohort Comparison Results",
        default_value="false",
        field_type="checkbox",
        group="features"
    ))
    atlas.add_field(ConfigField(
        "ATLAS_PLP_RESULTS_ENABLED",
        "Enable PLP Results",
        default_value="false",
        field_type="checkbox",
        group="features"
    ))
    sections.append(atlas)

    # WebAPI Configuration
    webapi = ConfigSection(
        "WebAPI",
        "WebAPI Configuration",
        "Configure OHDSI WebAPI settings"
    )
    webapi.add_group("basic", "Basic Settings")
    webapi.add_group("logging", "Logging Configuration")
    webapi.add_group("database", "Database Connection")
    
    # Basic Settings
    webapi.add_field(ConfigField(
        "FLYWAY_BASELINE_ON_MIGRATE",
        "Enable Flyway Baseline on Migrate",
        default_value="true",
        field_type="checkbox",
        help_text="Set to false if not using a pre-filled WebAPI schema",
        group="basic"
    ))
    
    # Logging Settings
    webapi.add_field(ConfigField(
        "WEBAPI_LOGGING_LEVEL_ROOT",
        "Root Logging Level",
        default_value="info",
        options=["trace", "debug", "info", "warn", "error"],
        field_type="combo",
        help_text="Logging level for the entire application",
        group="logging"
    ))
    webapi.add_field(ConfigField(
        "WEBAPI_LOGGING_LEVEL_ORG_OHDSI",
        "OHDSI Library Logging Level",
        default_value="info",
        options=["trace", "debug", "info", "warn", "error"],
        field_type="combo",
        help_text="Logging level for OHDSI libraries",
        group="logging"
    ))
    
    # Database Settings
    webapi.add_field(ConfigField(
        "WEBAPI_DATASOURCE_URL",
        "Database URL",
        default_value="jdbc:postgresql://broadsea-atlasdb:5432/postgres",
        help_text="Keep as-is if using Broadsea to launch WebAPI postgres, replace if using external instance",
        group="database"
    ))
    webapi.add_field(ConfigField(
        "WEBAPI_DATASOURCE_USERNAME",
        "Database Username",
        default_value="postgres",
        group="database"
    ))
    webapi.add_field(ConfigField(
        "WEBAPI_DATASOURCE_PASSWORD_FILE",
        "Database Password File",
        default_value="./secrets/webapi/WEBAPI_DATASOURCE_PASSWORD",
        field_type="file",
        help_text="Path to file containing database password",
        group="database"
    ))
    sections.append(webapi)

    # Security Configuration
    security = ConfigSection(
        "Security",
        "Security Configuration",
        "Configure authentication and authorization settings"
    )
    security.add_group("provider", "Security Provider")
    security.add_group("db", "Database Authentication")
    security.add_group("ldap", "LDAP Authentication")
    
    # Provider Settings
    security.add_field(ConfigField(
        "ATLAS_SECURITY_PROVIDER_TYPE",
        "Security Provider Type",
        default_value="none",
        options=["none", "ad", "ldap", "kerberos", "openid", "cas", "oauth", "iap", "db"],
        field_type="combo",
        help_text="Type of security provider to use",
        group="provider"
    ))
    security.add_field(ConfigField(
        "ATLAS_SECURITY_PROVIDER_NAME",
        "Provider Display Name",
        default_value="none",
        help_text="What to call the provider in the Atlas GUI",
        group="provider"
    ))
    
    # Database Auth Settings
    security.add_field(ConfigField(
        "SECURITY_AUTH_JDBC_ENABLED",
        "Enable Database Authentication",
        default_value="false",
        field_type="checkbox",
        group="db"
    ))
    security.add_field(ConfigField(
        "SECURITY_DB_DATASOURCE_SCHEMA",
        "Security Database Schema",
        default_value="webapi_security",
        depends_on={"SECURITY_AUTH_JDBC_ENABLED": "true"},
        group="db"
    ))
    
    # LDAP Settings
    security.add_field(ConfigField(
        "SECURITY_AUTH_LDAP_ENABLED",
        "Enable LDAP Authentication",
        default_value="false",
        field_type="checkbox",
        group="ldap"
    ))
    security.add_field(ConfigField(
        "SECURITY_LDAP_URL",
        "LDAP Server URL",
        default_value="ldap://broadsea-openldap:1389",
        depends_on={"SECURITY_AUTH_LDAP_ENABLED": "true"},
        group="ldap"
    ))
    sections.append(security)

    # Data Source Configuration
    datasource = ConfigSection(
        "DataSource",
        "Data Source Configuration",
        "Configure database connections for OMOP CDM"
    )
    datasource.add_group("connection", "Database Connection")
    datasource.add_group("vocab", "Vocabulary Settings")
    
    # Connection Settings
    datasource.add_field(ConfigField(
        "CDM_CONNECTIONDETAILS_DBMS",
        "Database Type",
        default_value="postgresql",
        options=["postgresql", "sql server", "oracle", "redshift"],
        field_type="combo",
        group="connection"
    ))
    datasource.add_field(ConfigField(
        "CDM_CONNECTIONDETAILS_SERVER",
        "Database Server",
        default_value="broadsea-atlasdb/postgres",
        group="connection"
    ))
    datasource.add_field(ConfigField(
        "CDM_CONNECTIONDETAILS_USER",
        "Database Username",
        default_value="postgres",
        group="connection"
    ))
    datasource.add_field(ConfigField(
        "CDM_CONNECTIONDETAILS_PASSWORD_FILE",
        "Database Password File",
        default_value="./secrets/postprocessing/CDM_CONNECTIONDETAILS_PASSWORD",
        field_type="file",
        group="connection"
    ))
    
    # Vocabulary Settings
    datasource.add_field(ConfigField(
        "VOCAB_DATABASE_SCHEMA",
        "Vocabulary Schema",
        default_value="demo_cdm",
        group="vocab"
    ))
    sections.append(datasource)

    # Build Configuration
    build = ConfigSection(
        "Build",
        "Build Configuration",
        "Configure building Atlas and WebAPI from Git"
    )
    build.add_group("atlas", "Atlas Build")
    build.add_group("webapi", "WebAPI Build")
    
    # Atlas Build Settings
    build.add_field(ConfigField(
        "ATLAS_GITHUB_URL",
        "Atlas Git URL",
        default_value="https://github.com/OHDSI/Atlas.git#1297c137669f21babace1906f23c3a9d70a9da19",
        help_text="Git URL with commit hash for building Atlas from source",
        group="atlas"
    ))
    
    # WebAPI Build Settings
    build.add_field(ConfigField(
        "WEBAPI_GITHUB_URL",
        "WebAPI Git URL",
        default_value="https://github.com/OHDSI/WebAPI.git#rc-2.13.0",
        help_text="Git URL with commit hash for building WebAPI from source",
        group="webapi"
    ))
    build.add_field(ConfigField(
        "WEBAPI_MAVEN_PROFILE",
        "Maven Profile",
        default_value="webapi-docker",
        help_text="Set to webapi-docker,webapi-solr if you want to enable SOLR Vocab search",
        group="webapi"
    ))
    sections.append(build)

    # SOLR Vocab Configuration
    solr = ConfigSection(
        "SOLR",
        "SOLR Vocabulary Configuration",
        "Configure SOLR OMOP Vocabulary search (optional)"
    )
    solr.add_group("endpoint", "SOLR Endpoint")
    solr.add_group("vocab", "Vocabulary Settings")
    
    # Endpoint Settings
    solr.add_field(ConfigField(
        "SOLR_VOCAB_ENDPOINT",
        "SOLR Endpoint URL",
        default_value="",
        required=False,
        help_text="Keep blank if not using Solr Vocab, use http://broadsea-solr-vocab:8983/solr if using Broadsea SOLR",
        group="endpoint"
    ))
    
    # Vocabulary Settings
    solr.add_field(ConfigField(
        "SOLR_VOCAB_VERSION",
        "Vocabulary Version",
        default_value="v5.0_23-JAN-23",
        help_text="Replace spaces with underscores",
        depends_on={"SOLR_VOCAB_ENDPOINT": lambda x: bool(x)},
        group="vocab"
    ))
    solr.add_field(ConfigField(
        "SOLR_VOCAB_DATABASE_SCHEMA",
        "Vocabulary Schema",
        default_value="vocab",
        depends_on={"SOLR_VOCAB_ENDPOINT": lambda x: bool(x)},
        group="vocab"
    ))
    sections.append(solr)

    # HADES Configuration
    hades = ConfigSection(
        "HADES",
        "HADES Configuration",
        "Configure HADES credentials for RStudio"
    )
    hades.add_group("auth", "Authentication")
    
    # Authentication Settings
    hades.add_field(ConfigField(
        "HADES_USER",
        "HADES Username",
        default_value="ohdsi",
        group="auth"
    ))
    hades.add_field(ConfigField(
        "HADES_PASSWORD_FILE",
        "Password File",
        default_value="./secrets/hades/HADES_PASSWORD",
        field_type="file",
        help_text="Path to file containing HADES password",
        group="auth"
    ))
    sections.append(hades)

    # Postgres and UMLS Configuration
    vocab = ConfigSection(
        "VocabDB",
        "Vocabulary Database Configuration",
        "Configure Postgres and UMLS credentials for loading OMOP Vocab files"
    )
    vocab.add_group("postgres", "Postgres Settings")
    vocab.add_group("umls", "UMLS Settings")
    
    # Postgres Settings
    vocab.add_field(ConfigField(
        "VOCAB_PG_HOST",
        "Database Host",
        default_value="broadsea-atlasdb",
        help_text="Host name without database name",
        group="postgres"
    ))
    vocab.add_field(ConfigField(
        "VOCAB_PG_DATABASE",
        "Database Name",
        default_value="postgres",
        group="postgres"
    ))
    vocab.add_field(ConfigField(
        "VOCAB_PG_SCHEMA",
        "Schema Name",
        default_value="omop_vocab",
        group="postgres"
    ))
    vocab.add_field(ConfigField(
        "VOCAB_PG_USER",
        "Username",
        default_value="postgres",
        group="postgres"
    ))
    vocab.add_field(ConfigField(
        "VOCAB_PG_PASSWORD_FILE",
        "Password File",
        default_value="./secrets/omop_vocab/VOCAB_PG_PASSWORD",
        field_type="file",
        group="postgres"
    ))
    vocab.add_field(ConfigField(
        "VOCAB_PG_FILES_PATH",
        "Vocabulary Files Path",
        default_value="./omop_vocab/files",
        help_text="Folder path with vocab files from Athena",
        field_type="file",
        group="postgres"
    ))
    
    # UMLS Settings
    vocab.add_field(ConfigField(
        "UMLS_API_KEY_FILE",
        "UMLS API Key File",
        default_value="./secrets/omop_vocab/UMLS_API_KEY",
        help_text="API KEY from UMLS account profile if CPT4 conversion needed",
        field_type="file",
        required=False,
        group="umls"
    ))
    sections.append(vocab)

    # Phoebe Configuration
    phoebe = ConfigSection(
        "Phoebe",
        "Phoebe Configuration",
        "Configure Postgres credentials for loading Phoebe file for Atlas Concept Recommendations"
    )
    phoebe.add_group("database", "Database Settings")
    
    # Database Settings
    phoebe.add_field(ConfigField(
        "PHOEBE_PG_HOST",
        "Database Host",
        default_value="broadsea-atlasdb",
        help_text="Host name without database name",
        group="database"
    ))
    phoebe.add_field(ConfigField(
        "PHOEBE_PG_DATABASE",
        "Database Name",
        default_value="postgres",
        group="database"
    ))
    phoebe.add_field(ConfigField(
        "PHOEBE_PG_SCHEMA",
        "Schema Name",
        default_value="omop_vocab",
        help_text="Should be an existing OMOP Vocabulary schema",
        group="database"
    ))
    phoebe.add_field(ConfigField(
        "PHOEBE_PG_USER",
        "Username",
        default_value="postgres",
        group="database"
    ))
    phoebe.add_field(ConfigField(
        "PHOEBE_PG_PASSWORD_FILE",
        "Password File",
        default_value="./secrets/phoebe/PHOEBE_PG_PASSWORD",
        field_type="file",
        group="database"
    ))
    sections.append(phoebe)

    # Ares Configuration
    ares = ConfigSection(
        "Ares",
        "Ares Configuration",
        "Configure Ares Data Folder"
    )
    ares.add_group("data", "Data Settings")
    
    # Data Settings
    ares.add_field(ConfigField(
        "ARES_DATA_FOLDER",
        "Data Folder Path",
        default_value="cdm-postprocessing-data",
        help_text="Path to the Ares data folder on your host",
        group="data"
    ))
    sections.append(ares)

    # Content Page Configuration
    content = ConfigSection(
        "Content",
        "Content Page Configuration",
        "Configure Broadsea Content Page settings"
    )
    content.add_group("basic", "Basic Settings")
    content.add_group("display", "Display Settings")
    
    # Basic Settings
    content.add_field(ConfigField(
        "CONTENT_TITLE",
        "Page Title",
        default_value="Broadsea 3.5 Applications",
        help_text="Can change this title to something for your organization",
        group="basic"
    ))
    
    # Display Settings
    for app in ["ARES", "ATLAS", "HADES", "OPENSHINYSERVER", "PGADMIN4", "POSITCONNECT", "PERSEUS"]:
        content.add_field(ConfigField(
            f"CONTENT_{app}_DISPLAY",
            f"Show {app}",
            default_value="show" if app not in ["POSITCONNECT", "PERSEUS"] else "none",
            options=["show", "none"],
            field_type="combo",
            help_text=f"{'Requires commercial license' if app == 'POSITCONNECT' else ''}",
            group="display"
        ))
    sections.append(content)

    # OpenLDAP Configuration
    ldap = ConfigSection(
        "OpenLDAP",
        "OpenLDAP Configuration",
        "Configure OpenLDAP for testing Atlas with security"
    )
    ldap.add_group("auth", "Authentication")
    
    # Authentication Settings
    ldap.add_field(ConfigField(
        "OPENLDAP_USERS",
        "LDAP Users",
        default_value="user1",
        help_text="Comma separated list of users",
        group="auth"
    ))
    ldap.add_field(ConfigField(
        "OPENLDAP_ADMIN_PASSWORD_FILE",
        "Admin Password File",
        default_value="./secrets/openldap/OPENLDAP_ADMIN_PASSWORD",
        field_type="file",
        group="auth"
    ))
    ldap.add_field(ConfigField(
        "OPENLDAP_ACCOUNT_PASSWORDS_FILE",
        "Account Passwords File",
        default_value="./secrets/openldap/OPENLDAP_ACCOUNT_PASSWORDS",
        field_type="file",
        group="auth"
    ))
    sections.append(ldap)

    # Shiny Server Configuration
    shiny = ConfigSection(
        "ShinyServer",
        "Open Shiny Server Configuration",
        "Configure open-source Shiny Server"
    )
    shiny.add_group("basic", "Basic Settings")
    
    # Basic Settings
    shiny.add_field(ConfigField(
        "OPEN_SHINY_SERVER_APP_ROOT",
        "App Root Directory",
        default_value="./shiny_server",
        help_text="Root folder containing Shiny apps",
        field_type="file",
        group="basic"
    ))
    sections.append(shiny)

    # Posit Connect Configuration
    posit = ConfigSection(
        "PositConnect",
        "Posit Connect Configuration",
        "Configure Posit Connect (requires commercial license)"
    )
    posit.add_group("license", "License Settings")
    posit.add_group("config", "Configuration Settings")
    
    # License Settings
    posit.add_field(ConfigField(
        "POSIT_CONNECT_LICENSE_SERVER",
        "License Server URL",
        default_value="",
        required=False,
        help_text="Server URL that hosts the license",
        group="license"
    ))
    posit.add_field(ConfigField(
        "POSIT_CONNECT_LICENSE_FILE",
        "License File",
        default_value="./posit_connect/posit_license.lic",
        field_type="file",
        help_text="Path to license file",
        group="license"
    ))
    
    # Configuration Settings
    posit.add_field(ConfigField(
        "POSIT_CONNECT_GCFG_FILE",
        "Global Config File",
        default_value="./posit_connect/rstudio-connect.gcfg",
        field_type="file",
        help_text="Global configuration file for Posit Connect",
        group="config"
    ))
    posit.add_field(ConfigField(
        "POSIT_CONNECT_R_VERSION",
        "R Version",
        default_value="4.2.3",
        help_text="R version to use (versions listed at https://cdn.posit.co/r/versions.json)",
        group="config"
    ))
    sections.append(posit)

    # Perseus Configuration
    perseus = ConfigSection(
        "Perseus",
        "Perseus Configuration",
        "Configure Perseus for ETL design and execution"
    )
    perseus.add_group("email", "Email Settings")
    perseus.add_group("security", "Security Settings")
    perseus.add_group("vocab", "Vocabulary Settings")
    
    # Email Settings
    perseus.add_field(ConfigField(
        "PERSEUS_SMTP_SERVER",
        "SMTP Server",
        default_value="",
        required=False,
        group="email"
    ))
    perseus.add_field(ConfigField(
        "PERSEUS_SMTP_PORT",
        "SMTP Port",
        default_value="",
        required=False,
        validation_func=lambda x: not x or (x.isdigit() and 0 <= int(x) <= 65535),
        group="email"
    ))
    
    # Security Settings
    perseus.add_field(ConfigField(
        "PERSEUS_TOKEN_SECRET_KEY",
        "Token Secret Key",
        default_value="Perseus-Arcad!a",
        group="security"
    ))
    perseus.add_field(ConfigField(
        "PERSEUS_EMAIL_SECRET_KEY",
        "Email Secret Key",
        default_value="8cmuh4t5xTtR1EHaojWL0aqCR3vZ48PZF5AYkTe0iqo=",
        group="security"
    ))
    
    # Vocabulary Settings
    perseus.add_field(ConfigField(
        "PERSEUS_VOCAB_FILES_PATH",
        "Vocabulary Files Path",
        default_value="./omop_vocab/files",
        field_type="file",
        group="vocab"
    ))
    sections.append(perseus)

    # Post-Processing Configuration
    postproc = ConfigSection(
        "PostProcessing",
        "Post-Processing Configuration",
        "Configure CDM post-processing tools (Achilles, DQD, AresIndexer)"
    )
    postproc.add_group("achilles", "Achilles Settings")
    postproc.add_group("dqd", "Data Quality Dashboard Settings")
    postproc.add_group("ares", "Ares Indexer Settings")
    
    # Achilles Settings
    postproc.add_field(ConfigField(
        "ACHILLES_CREATE_TABLE",
        "Create Tables",
        default_value="true",
        field_type="checkbox",
        group="achilles"
    ))
    postproc.add_field(ConfigField(
        "ACHILLES_SMALL_CELL_COUNT",
        "Small Cell Count",
        default_value="0",
        validation_func=lambda x: x.isdigit(),
        group="achilles"
    ))
    
    # DQD Settings
    postproc.add_field(ConfigField(
        "DQD_NUM_THREADS",
        "Number of Threads",
        default_value="2",
        validation_func=lambda x: x.isdigit() and int(x) > 0,
        group="dqd"
    ))
    postproc.add_field(ConfigField(
        "DQD_WRITE_TO_TABLE",
        "Write to Table",
        default_value="TRUE",
        field_type="checkbox",
        group="dqd"
    ))
    
    # Ares Settings
    postproc.add_field(ConfigField(
        "ARES_RUN_NETWORK",
        "Run Network Analysis",
        default_value="FALSE",
        field_type="checkbox",
        help_text="Should the full Ares network analysis be run?",
        group="ares"
    ))
    sections.append(postproc)

    # pgAdmin Configuration
    pgadmin = ConfigSection(
        "pgAdmin",
        "pgAdmin Configuration",
        "Configure pgAdmin4 settings"
    )
    pgadmin.add_group("auth", "Authentication")
    
    # Authentication Settings
    pgadmin.add_field(ConfigField(
        "PGADMIN_ADMIN_USER",
        "Admin Email",
        default_value="user@domain.com",
        validation_func=lambda x: "@" in x,
        group="auth"
    ))
    pgadmin.add_field(ConfigField(
        "PGADMIN_DEFAULT_PASSWORD_FILE",
        "Password File",
        default_value="./secrets/pgadmin4/PGADMIN_DEFAULT_PASSWORD",
        field_type="file",
        group="auth"
    ))
    sections.append(pgadmin)

    return sections

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show wizard
    sections = create_sections()
    wizard = ConfigWizard(sections)
    wizard.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
