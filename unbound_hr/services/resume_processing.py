import re
from pathlib import Path

import frappe
from frappe import _


COMMON_SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "node.js",
    "fastapi",
    "django",
    "flask",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "git",
    "github",
    "pytorch",
    "tensorflow",
    "scikit-learn",
    "pandas",
    "numpy",
    "machine learning",
    "deep learning",
    "computer vision",
    "nlp",
    "rest api",
    "graphql",
    "linux",
]


def normalize_text(text):
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip().lower()


def extract_text_from_attachment(file_url):
    if not file_url:
        frappe.throw(_("Resume attachment is missing."))

    file_doc = frappe.get_doc(
        "File",
        {"file_url": file_url},
    )

    file_path = file_doc.get_full_path()
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    if extension in {".docx"}:
        return extract_docx_text(file_path)

    if extension in {".txt"}:
        return Path(file_path).read_text(
            encoding="utf-8",
            errors="ignore",
        )

    frappe.throw(
        _("Unsupported resume format: {0}").format(extension)
    )


def extract_pdf_text(file_path):
    try:
        from pypdf import PdfReader
    except ImportError:
        frappe.throw(
            _("pypdf is not installed in the current image.")
        )

    reader = PdfReader(file_path)

    text = []

    for page in reader.pages:
        text.append(page.extract_text() or "")

    return "\n".join(text)


def extract_docx_text(file_path):
    try:
        from docx import Document
    except ImportError:
        frappe.throw(
            _("python-docx is not installed in the current image.")
        )

    document = Document(file_path)

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )


def extract_skills(text):
    normalized = normalize_text(text)

    found = []

    for skill in COMMON_SKILLS:
        if skill in normalized:
            found.append(skill)

    return sorted(set(found))


def extract_years_experience(text):
    normalized = normalize_text(text)

    year_patterns = [
        # 3 years of experience
        # 3+ years of experience
        r"(\d+(?:\.\d+)?)\+?\s+years?\s+of\s+experience",

        # 1 year of project experience
        # 2 years of professional experience
        # 3 years of relevant work experience
        r"(\d+(?:\.\d+)?)\+?\s+years?\s+of\s+(?:relevant\s+|professional\s+|project\s+|work\s+|industry\s+|hands[- ]on\s+|practical\s+)*experience",

        # 2 years professional experience
        # 1 year project experience
        r"(\d+(?:\.\d+)?)\+?\s+years?\s+(?:relevant\s+|professional\s+|project\s+|work\s+|industry\s+|hands[- ]on\s+|practical\s+)*experience",

        # Experience: 3 years
        r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\+?\s+years?",
    ]

    month_patterns = [
        # 6 months experience
        # 18 months of work experience
        r"(\d+(?:\.\d+)?)\s+months?\s+(?:of\s+)?(?:relevant\s+|professional\s+|project\s+|work\s+|industry\s+|hands[- ]on\s+|practical\s+)*experience",
    ]

    values = []

    for pattern in year_patterns:
        matches = re.findall(pattern, normalized)

        for match in matches:
            try:
                values.append(float(match))
            except (TypeError, ValueError):
                continue

    for pattern in month_patterns:
        matches = re.findall(pattern, normalized)

        for match in matches:
            try:
                months = float(match)
                values.append(months / 12.0)
            except (TypeError, ValueError):
                continue

    return round(max(values), 2) if values else 0.0


def extract_education_signals(text):
    normalized = normalize_text(text)

    signals = []

    education_terms = {
        "phd": ["phd", "doctor of philosophy"],
        "masters": [
            "master of technology",
            "m.tech",
            "mtech",
            "master of science",
            "m.sc",
            "msc",
            "mba",
        ],
        "bachelors": [
            "bachelor of technology",
            "b.tech",
            "btech",
            "bachelor of engineering",
            "b.e.",
            "bachelor of science",
            "b.sc",
            "bsc",
        ],
        "diploma": [
            "diploma",
        ],
    }

    for level, terms in education_terms.items():
        if any(term in normalized for term in terms):
            signals.append(level)

    return signals


def parse_resume(text):
    return {
        "skills": extract_skills(text),
        "years_experience": extract_years_experience(text),
        "education": extract_education_signals(text),
        "raw_text": text,
    }
