import os
import sys
from PyQt6 import QtWidgets

from app.features.letter_explainer import explain_letter
from app.features.form_helper import fill_form_to_pdf
from app.features.textbook_builder import TextbookSpec, build_textbook


class LetterTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.path_edit = QtWidgets.QLineEdit("content/letters/sample_medi_cal.pdf")
        self.choose_btn = QtWidgets.QPushButton("Choose File…")
        self.run_btn = QtWidgets.QPushButton("Explain Letter")
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)

        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(self.path_edit)
        hl.addWidget(self.choose_btn)
        layout.addLayout(hl)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.output)

        self.choose_btn.clicked.connect(self.choose_file)
        self.run_btn.clicked.connect(self.run)

    def choose_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select letter", "content/letters", "PDF/TXT (*.pdf *.txt)")
        if path:
            self.path_edit.setText(path)

    def run(self):
        path = self.path_edit.text().strip()
        res = explain_letter(path)
        self.output.setPlainText(f"Summary\n{res.summary}\n\nChecklist\n{res.checklist}")


class FormTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.schema_edit = QtWidgets.QLineEdit("content/forms/snap.yaml")
        self.out_edit = QtWidgets.QLineEdit("out/filled.pdf")
        self.interactive = QtWidgets.QCheckBox("Interactive mode")
        self.choose_schema_btn = QtWidgets.QPushButton("Choose Schema…")
        self.choose_out_btn = QtWidgets.QPushButton("Save As…")
        self.run_btn = QtWidgets.QPushButton("Fill Form")
        self.status = QtWidgets.QLabel()

        gl = QtWidgets.QGridLayout()
        gl.addWidget(QtWidgets.QLabel("Schema"), 0, 0)
        gl.addWidget(self.schema_edit, 0, 1)
        gl.addWidget(self.choose_schema_btn, 0, 2)
        gl.addWidget(QtWidgets.QLabel("Output PDF"), 1, 0)
        gl.addWidget(self.out_edit, 1, 1)
        gl.addWidget(self.choose_out_btn, 1, 2)
        gl.addWidget(self.interactive, 2, 1)
        layout.addLayout(gl)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.status)

        self.choose_schema_btn.clicked.connect(self.choose_schema)
        self.choose_out_btn.clicked.connect(self.choose_out)
        self.run_btn.clicked.connect(self.run)

    def choose_schema(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select schema", "content/forms", "YAML (*.yaml *.yml)")
        if path:
            self.schema_edit.setText(path)

    def choose_out(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save PDF", "out/filled.pdf", "PDF (*.pdf)")
        if path:
            self.out_edit.setText(path)

    def run(self):
        try:
            out, _answers = fill_form_to_pdf(self.schema_edit.text().strip(), self.out_edit.text().strip(), interactive=self.interactive.isChecked())
            self.status.setText(f"Wrote {out}")
        except Exception as e:
            self.status.setText(str(e))


class TextbookTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.grade = QtWidgets.QSpinBox()
        self.grade.setRange(1, 12)
        self.grade.setValue(5)
        self.lang = QtWidgets.QLineEdit("es")
        self.topic = QtWidgets.QLineEdit("fractions")
        self.out = QtWidgets.QLineEdit("out/textbook_g5_es_fractions.epub")
    self.mode = QtWidgets.QComboBox()
    self.mode.addItems(["sample", "full"])
    self.mode.setCurrentText("sample")
        self.run_btn = QtWidgets.QPushButton("Build Textbook")
        self.status = QtWidgets.QLabel()

        form = QtWidgets.QFormLayout()
        form.addRow("Grade", self.grade)
        form.addRow("Language", self.lang)
        form.addRow("Topic", self.topic)
    form.addRow("Mode", self.mode)
        form.addRow("Output", self.out)
        layout.addLayout(form)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.status)

        self.run_btn.clicked.connect(self.run)

    def run(self):
        spec = TextbookSpec(grade=self.grade.value(), language=self.lang.text().strip(), topic=self.topic.text().strip())
        dest = self.out.text().strip()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
    path = build_textbook(spec, dest, mode=self.mode.currentText())
        self.status.setText(f"Wrote {path}")


class Main(QtWidgets.QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlainText.ink MVP")
        self.addTab(LetterTab(), "Letter Explainer")
        self.addTab(FormTab(), "Form Helper")
        self.addTab(TextbookTab(), "Textbook Builder")


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = Main()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

