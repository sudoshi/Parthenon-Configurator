from base_config import BaseConfigSection
from PyQt6.QtWidgets import QFormLayout

class WebAPISection(BaseConfigSection):
    """WebAPI configuration section"""

    def __init__(self):
        self.section_name = "WebAPI"
        super().__init__()

    def setup_fields(self, form_layout: QFormLayout):
        """Setup WebAPI configuration fields"""
        self.add_field(form_layout, "WEBAPI_VERSION", default="2.12.0")
        self.add_field(form_layout, "WEBAPI_PORT", default="8081")
        self.add_field(form_layout, "WEBAPI_CONTEXT_PATH", default="/WebAPI")
        self.add_field(form_layout, "WEBAPI_DB_HOST", default="postgres")
        self.add_field(form_layout, "WEBAPI_DB_PORT", default="5432")
        self.add_field(form_layout, "WEBAPI_DB_NAME", default="ohdsi")
        self.add_field(form_layout, "WEBAPI_DB_USER", default="postgres")
        self.add_field(form_layout, "WEBAPI_DB_PASS", default="postgres")
        self.add_field(form_layout, "WEBAPI_DATASOURCES_JSON", default="[]")
        self.add_field(form_layout, "WEBAPI_CORS_ENABLED", default="true")
        self.add_field(form_layout, "WEBAPI_SECURITY_ENABLED", default="false")

    def validate(self) -> list[str]:
        """Validate WebAPI configuration"""
        issues = []
        
        # Validate port numbers
        for port_field in ["WEBAPI_PORT", "WEBAPI_DB_PORT"]:
            port = self.fields[port_field].text()
            if not port.isdigit():
                issues.append(f"{port_field} must be a number")
            elif not (0 <= int(port) <= 65535):
                issues.append(f"{port_field} must be between 0 and 65535")

        # Validate JSON
        try:
            import json
            json.loads(self.fields["WEBAPI_DATASOURCES_JSON"].text())
        except json.JSONDecodeError:
            issues.append("WEBAPI_DATASOURCES_JSON must be valid JSON")

        # Validate boolean fields
        for bool_field in ["WEBAPI_CORS_ENABLED", "WEBAPI_SECURITY_ENABLED"]:
            value = self.fields[bool_field].text().lower()
            if value not in ["true", "false"]:
                issues.append(f"{bool_field} must be either 'true' or 'false'")

        return issues
