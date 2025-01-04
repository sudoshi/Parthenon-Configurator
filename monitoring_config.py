from base_config import BaseConfigSection
from PyQt6.QtWidgets import QFormLayout

class MonitoringSection(BaseConfigSection):
    """Monitoring configuration section"""

    def __init__(self):
        self.section_name = "Monitoring"
        super().__init__()

    def setup_fields(self, form_layout: QFormLayout):
        """Setup monitoring configuration fields"""
        self.add_field(form_layout, "MONITORING_ENABLED", default="true")
        self.add_field(form_layout, "MONITORING_PORT", default="9090")
        self.add_field(form_layout, "MONITORING_PATH", default="/metrics")
        self.add_field(form_layout, "MONITORING_INTERVAL", default="15")
        self.add_field(form_layout, "MONITORING_RETENTION_DAYS", default="30")
        self.add_field(form_layout, "MONITORING_LOG_LEVEL", default="info")
        self.add_field(form_layout, "MONITORING_ALERT_EMAIL", default="")
        self.add_field(form_layout, "MONITORING_ALERT_SLACK", default="")
        self.add_field(form_layout, "MONITORING_DISK_THRESHOLD", default="90")
        self.add_field(form_layout, "MONITORING_MEMORY_THRESHOLD", default="85")
        self.add_field(form_layout, "MONITORING_CPU_THRESHOLD", default="80")

    def validate(self) -> list[str]:
        """Validate monitoring configuration"""
        issues = []
        
        # Validate boolean fields
        value = self.fields["MONITORING_ENABLED"].text().lower()
        if value not in ["true", "false"]:
            issues.append("MONITORING_ENABLED must be either 'true' or 'false'")

        # Validate port number
        port = self.fields["MONITORING_PORT"].text()
        if not port.isdigit():
            issues.append("MONITORING_PORT must be a number")
        elif not (0 <= int(port) <= 65535):
            issues.append("MONITORING_PORT must be between 0 and 65535")

        # Validate numeric fields
        numeric_fields = {
            "MONITORING_INTERVAL": (1, 3600, "seconds"),
            "MONITORING_RETENTION_DAYS": (1, 365, "days"),
            "MONITORING_DISK_THRESHOLD": (0, 100, "percent"),
            "MONITORING_MEMORY_THRESHOLD": (0, 100, "percent"),
            "MONITORING_CPU_THRESHOLD": (0, 100, "percent")
        }

        for field, (min_val, max_val, unit) in numeric_fields.items():
            value = self.fields[field].text()
            if not value.isdigit():
                issues.append(f"{field} must be a number")
            else:
                num_value = int(value)
                if not (min_val <= num_value <= max_val):
                    issues.append(f"{field} must be between {min_val} and {max_val} {unit}")

        # Validate log level
        valid_log_levels = ["debug", "info", "warning", "error", "critical"]
        log_level = self.fields["MONITORING_LOG_LEVEL"].text().lower()
        if log_level not in valid_log_levels:
            issues.append(f"MONITORING_LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")

        # Validate email format if provided
        email = self.fields["MONITORING_ALERT_EMAIL"].text()
        if email and '@' not in email:
            issues.append("MONITORING_ALERT_EMAIL must be a valid email address")

        # Validate Slack webhook URL format if provided
        slack_url = self.fields["MONITORING_ALERT_SLACK"].text()
        if slack_url and not (slack_url.startswith("https://hooks.slack.com/") or not slack_url):
            issues.append("MONITORING_ALERT_SLACK must be a valid Slack webhook URL")

        return issues
