from base_config import BaseConfigSection
from PyQt6.QtWidgets import QFormLayout

class SecuritySection(BaseConfigSection):
    """Security configuration section"""

    def __init__(self):
        self.section_name = "Security"
        super().__init__()

    def setup_fields(self, form_layout: QFormLayout):
        """Setup security configuration fields"""
        self.add_field(form_layout, "SECURITY_ENABLED", default="false")
        self.add_field(form_layout, "SECURITY_AUTH_PROVIDER", default="db")
        self.add_field(form_layout, "SECURITY_DB_HOST", default="postgres")
        self.add_field(form_layout, "SECURITY_DB_PORT", default="5432")
        self.add_field(form_layout, "SECURITY_DB_NAME", default="security")
        self.add_field(form_layout, "SECURITY_DB_USER", default="postgres")
        self.add_field(form_layout, "SECURITY_DB_PASS", default="postgres")
        self.add_field(form_layout, "SECURITY_OAUTH_CLIENT_ID", default="")
        self.add_field(form_layout, "SECURITY_OAUTH_CLIENT_SECRET", default="")
        self.add_field(form_layout, "SECURITY_OAUTH_CALLBACK_URL", default="")
        self.add_field(form_layout, "SECURITY_SSL_ENABLED", default="false")
        self.add_field(form_layout, "SECURITY_SSL_KEYSTORE", default="")
        self.add_field(form_layout, "SECURITY_SSL_KEYSTORE_PASSWORD", default="")

    def validate(self) -> list[str]:
        """Validate security configuration"""
        issues = []
        
        # Validate port number
        port = self.fields["SECURITY_DB_PORT"].text()
        if not port.isdigit():
            issues.append("SECURITY_DB_PORT must be a number")
        elif not (0 <= int(port) <= 65535):
            issues.append("SECURITY_DB_PORT must be between 0 and 65535")

        # Validate boolean fields
        for bool_field in ["SECURITY_ENABLED", "SECURITY_SSL_ENABLED"]:
            value = self.fields[bool_field].text().lower()
            if value not in ["true", "false"]:
                issues.append(f"{bool_field} must be either 'true' or 'false'")

        # Validate auth provider
        auth_provider = self.fields["SECURITY_AUTH_PROVIDER"].text().lower()
        if auth_provider not in ["db", "oauth", "ldap"]:
            issues.append("SECURITY_AUTH_PROVIDER must be one of: db, oauth, ldap")

        # Validate OAuth settings if OAuth is selected
        if auth_provider == "oauth":
            oauth_fields = [
                "SECURITY_OAUTH_CLIENT_ID",
                "SECURITY_OAUTH_CLIENT_SECRET",
                "SECURITY_OAUTH_CALLBACK_URL"
            ]
            for field in oauth_fields:
                if not self.fields[field].text().strip():
                    issues.append(f"{field} is required when using OAuth")

        # Validate SSL settings if SSL is enabled
        if self.fields["SECURITY_SSL_ENABLED"].text().lower() == "true":
            ssl_fields = ["SECURITY_SSL_KEYSTORE", "SECURITY_SSL_KEYSTORE_PASSWORD"]
            for field in ssl_fields:
                if not self.fields[field].text().strip():
                    issues.append(f"{field} is required when SSL is enabled")

        return issues
