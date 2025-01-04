from base_config import BaseConfigSection
from PyQt6.QtWidgets import QFormLayout

class BroadseaHostSection(BaseConfigSection):
    """Broadsea host configuration section"""

    def __init__(self):
        self.section_name = "Host"
        super().__init__()

    def setup_fields(self, form_layout: QFormLayout):
        """Setup host configuration fields"""
        self.add_field(form_layout, "HOST_NAME", default="localhost")
        self.add_field(form_layout, "HOST_PORT", default="8080")
        self.add_field(form_layout, "HOST_PROTOCOL", default="http")
        self.add_field(form_layout, "HOST_CONTEXT_PATH", default="/")

    def validate(self) -> list[str]:
        """Validate host configuration"""
        issues = []
        port = self.fields["HOST_PORT"].text()
        
        if not port.isdigit():
            issues.append("Port must be a number")
        elif not (0 <= int(port) <= 65535):
            issues.append("Port must be between 0 and 65535")

        protocol = self.fields["HOST_PROTOCOL"].text().lower()
        if protocol not in ["http", "https"]:
            issues.append("Protocol must be either 'http' or 'https'")

        return issues
