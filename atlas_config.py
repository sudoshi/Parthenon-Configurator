from base_config import BaseConfigSection
from PyQt6.QtWidgets import QFormLayout, QTextEdit

class AtlasGUISection(BaseConfigSection):
    """Atlas GUI configuration section"""

    def __init__(self):
        self.section_name = "Atlas"
        super().__init__()

    def setup_fields(self, form_layout: QFormLayout):
        """Setup Atlas configuration fields"""
        self.add_field(form_layout, "ATLAS_VERSION", default="2.12.0")
        self.add_field(form_layout, "ATLAS_PORT", default="8080")
        self.add_field(form_layout, "ATLAS_CONTEXT_PATH", default="/atlas")
        self.add_field(form_layout, "ATLAS_DB_HOST", default="postgres")
        self.add_field(form_layout, "ATLAS_DB_PORT", default="5432")
        self.add_field(form_layout, "ATLAS_DB_NAME", default="atlas")
        self.add_field(form_layout, "ATLAS_DB_USER", default="postgres")
        self.add_field(form_layout, "ATLAS_DB_PASS", default="postgres")
        self.add_field(form_layout, "ATLAS_CONFIG", field_type=QTextEdit, default="{}")

    def validate(self) -> list[str]:
        """Validate Atlas configuration"""
        issues = []
        
        # Validate port numbers
        for port_field in ["ATLAS_PORT", "ATLAS_DB_PORT"]:
            port = self.fields[port_field].text()
            if not port.isdigit():
                issues.append(f"{port_field} must be a number")
            elif not (0 <= int(port) <= 65535):
                issues.append(f"{port_field} must be between 0 and 65535")

        # Validate JSON config
        try:
            import json
            json.loads(self.fields["ATLAS_CONFIG"].toPlainText())
        except json.JSONDecodeError:
            issues.append("ATLAS_CONFIG must be valid JSON")

        return issues
