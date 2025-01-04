from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit
from typing import Dict, List

class BaseConfigSection(QWidget):
    """Base class for configuration sections"""
    
    def __init__(self):
        super().__init__()
        self.section_name = ""
        self.fields = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the section UI"""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        self.setup_fields(form_layout)

    def setup_fields(self, form_layout: QFormLayout):
        """Setup form fields - to be implemented by subclasses"""
        pass

    def add_field(self, form_layout: QFormLayout, name: str, field_type=QLineEdit, default=""):
        """Add a form field"""
        field = field_type()
        if isinstance(field, QLineEdit):
            field.setText(default)
        elif isinstance(field, QTextEdit):
            field.setPlainText(default)
        self.fields[name] = field
        form_layout.addRow(name, field)

    def reset_to_defaults(self):
        """Reset fields to default values"""
        for field in self.fields.values():
            if isinstance(field, QLineEdit):
                field.setText("")
            elif isinstance(field, QTextEdit):
                field.setPlainText("")

    def load_config(self, config: Dict[str, str]):
        """Load configuration into fields"""
        for name, field in self.fields.items():
            if name in config:
                if isinstance(field, QLineEdit):
                    field.setText(config[name])
                elif isinstance(field, QTextEdit):
                    field.setPlainText(config[name])

    def get_config(self) -> Dict[str, str]:
        """Get current configuration"""
        config = {}
        for name, field in self.fields.items():
            if isinstance(field, QLineEdit):
                config[name] = field.text()
            elif isinstance(field, QTextEdit):
                config[name] = field.toPlainText()
        return config

    def validate(self) -> List[str]:
        """Validate configuration - to be implemented by subclasses"""
        return []
