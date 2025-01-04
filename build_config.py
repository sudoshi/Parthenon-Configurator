from base_config import BaseConfigSection
from PyQt6.QtWidgets import QFormLayout

class BuildSection(BaseConfigSection):
    """Build configuration section"""

    def __init__(self):
        self.section_name = "Build"
        super().__init__()

    def setup_fields(self, form_layout: QFormLayout):
        """Setup build configuration fields"""
        self.add_field(form_layout, "BUILD_MODE", default="development")
        self.add_field(form_layout, "BUILD_CLEAN", default="false")
        self.add_field(form_layout, "BUILD_PARALLEL", default="true")
        self.add_field(form_layout, "BUILD_SKIP_TESTS", default="false")
        self.add_field(form_layout, "BUILD_SKIP_LINT", default="false")
        self.add_field(form_layout, "BUILD_SKIP_DOCS", default="false")
        self.add_field(form_layout, "BUILD_TARGET_DIR", default="./target")
        self.add_field(form_layout, "BUILD_JAVA_HOME", default="")
        self.add_field(form_layout, "BUILD_MAVEN_OPTS", default="-Xmx2g")
        self.add_field(form_layout, "BUILD_MAVEN_PROFILES", default="")

    def validate(self) -> list[str]:
        """Validate build configuration"""
        issues = []
        
        # Validate build mode
        valid_modes = ["development", "production", "test"]
        mode = self.fields["BUILD_MODE"].text().lower()
        if mode not in valid_modes:
            issues.append(f"BUILD_MODE must be one of: {', '.join(valid_modes)}")

        # Validate boolean fields
        bool_fields = [
            "BUILD_CLEAN", "BUILD_PARALLEL", "BUILD_SKIP_TESTS",
            "BUILD_SKIP_LINT", "BUILD_SKIP_DOCS"
        ]
        for field in bool_fields:
            value = self.fields[field].text().lower()
            if value not in ["true", "false"]:
                issues.append(f"{field} must be either 'true' or 'false'")

        # Validate memory option format
        maven_opts = self.fields["BUILD_MAVEN_OPTS"].text()
        if maven_opts:
            if not any(maven_opts.startswith(prefix) for prefix in ["-Xmx", "-Xms"]):
                issues.append("BUILD_MAVEN_OPTS must start with -Xmx or -Xms")
            if not any(maven_opts.endswith(suffix) for suffix in ["g", "m", "k"]):
                issues.append("BUILD_MAVEN_OPTS must end with g, m, or k")

        # Validate target directory path
        target_dir = self.fields["BUILD_TARGET_DIR"].text()
        if not target_dir.strip():
            issues.append("BUILD_TARGET_DIR cannot be empty")
        elif not target_dir.startswith((".", "/", "~/")):
            issues.append("BUILD_TARGET_DIR must be an absolute path or start with ./")

        return issues
