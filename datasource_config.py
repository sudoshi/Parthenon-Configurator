from base_config import BaseConfigSection
from PyQt6.QtWidgets import QFormLayout, QTextEdit

class DataSourceSection(BaseConfigSection):
    """Data source configuration section"""

    def __init__(self):
        self.section_name = "DataSource"
        super().__init__()

    def setup_fields(self, form_layout: QFormLayout):
        """Setup data source configuration fields"""
        self.add_field(form_layout, "DATASOURCE_NAME", default="OHDSI CDM")
        self.add_field(form_layout, "DATASOURCE_KEY", default="OHDSI")
        self.add_field(form_layout, "DATASOURCE_DIALECT", default="postgresql")
        self.add_field(form_layout, "DATASOURCE_DB_HOST", default="postgres")
        self.add_field(form_layout, "DATASOURCE_DB_PORT", default="5432")
        self.add_field(form_layout, "DATASOURCE_DB_NAME", default="cdm")
        self.add_field(form_layout, "DATASOURCE_DB_USER", default="postgres")
        self.add_field(form_layout, "DATASOURCE_DB_PASS", default="postgres")
        self.add_field(form_layout, "DATASOURCE_CDM_SCHEMA", default="cdm")
        self.add_field(form_layout, "DATASOURCE_VOCAB_SCHEMA", default="vocabulary")
        self.add_field(form_layout, "DATASOURCE_RESULTS_SCHEMA", default="results")
        self.add_field(form_layout, "DATASOURCE_TEMP_SCHEMA", default="temp")
        self.add_field(form_layout, "DATASOURCE_COHORT_TARGET_TABLE", default="cohort")
        self.add_field(form_layout, "DATASOURCE_ADVANCED_OPTIONS", field_type=QTextEdit, default="{}")

    def validate(self) -> list[str]:
        """Validate data source configuration"""
        issues = []
        
        # Validate port number
        port = self.fields["DATASOURCE_DB_PORT"].text()
        if not port.isdigit():
            issues.append("DATASOURCE_DB_PORT must be a number")
        elif not (0 <= int(port) <= 65535):
            issues.append("DATASOURCE_DB_PORT must be between 0 and 65535")

        # Validate dialect
        valid_dialects = ["postgresql", "sql server", "oracle", "redshift", "bigquery"]
        dialect = self.fields["DATASOURCE_DIALECT"].text().lower()
        if dialect not in valid_dialects:
            issues.append(f"DATASOURCE_DIALECT must be one of: {', '.join(valid_dialects)}")

        # Validate key format (alphanumeric and underscores only)
        key = self.fields["DATASOURCE_KEY"].text()
        if not key.replace('_', '').isalnum():
            issues.append("DATASOURCE_KEY must contain only letters, numbers, and underscores")

        # Validate advanced options JSON
        try:
            import json
            json.loads(self.fields["DATASOURCE_ADVANCED_OPTIONS"].toPlainText())
        except json.JSONDecodeError:
            issues.append("DATASOURCE_ADVANCED_OPTIONS must be valid JSON")

        # Validate required fields are not empty
        required_fields = [
            "DATASOURCE_NAME", "DATASOURCE_KEY", "DATASOURCE_CDM_SCHEMA",
            "DATASOURCE_VOCAB_SCHEMA", "DATASOURCE_RESULTS_SCHEMA"
        ]
        for field in required_fields:
            if not self.fields[field].text().strip():
                issues.append(f"{field} cannot be empty")

        return issues
