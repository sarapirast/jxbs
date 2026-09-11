"""
Resume-to-jobs matching: extract text from an uploaded PDF, detect known
technical skills against a curated keyword list, and build a focused
search query from what was found.

Deliberately NOT feeding the raw resume text into hybrid_search() as the
query: a full resume is much longer and noisier than the short queries
this system's BM25/embedding weights were tuned against
on.

The skill list below is a curated, non-exhaustive dictionary, a real
limitation worth naming honestly: it will miss skills it doesn't know
about, and match substrings loosely.
"""
import io
import re
from pypdf import PdfReader

SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    "sql", "html", "css",
    "react", "react native", "angular", "vue", "next.js", "node.js",
    "express", "django", "flask", "fastapi", "spring", "spring boot",
    ".net", "rails",
    "aws", "azure", "gcp", "google cloud", "lambda", "ec2", "s3", "rds",
    "dynamodb", "cloudfront", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "ci/cd", "github actions",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "sqlite", "bigquery", "snowflake",
    "pytorch", "tensorflow", "keras", "scikit-learn", "xgboost",
    "machine learning", "deep learning", "nlp", "computer vision",
    "reinforcement learning", "llm", "transformers", "opencv",
    "pandas", "numpy", "scipy", "matplotlib", "spark", "hadoop",
    "airflow", "kafka", "rabbitmq",
    "rest api", "graphql", "grpc", "microservices", "distributed systems",
    "system design", "data structures", "algorithms",
    "git", "linux", "bash", "agile", "scrum",
    "unit testing", "pytest", "junit", "tdd",
    "html5", "tailwind", "bootstrap", "sass",
    "ros", "ros2", "embedded", "firmware", "fpga", "verilog", "vhdl",
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_skills(resume_text: str) -> list[str]:
    text_lower = resume_text.lower()
    found = []
    seen = set()
    for skill in SKILL_KEYWORDS:
        if skill in seen:
            continue  # defensive: guards against an accidental duplicate entry in SKILL_KEYWORDS 
        if re.search(r"[a-z0-9]", skill) and skill.replace(".", "").replace("+", "").replace("#", "").isalnum():
            pattern = r"\b" + re.escape(skill) + r"\b"
        else:
            pattern = re.escape(skill)
        if re.search(pattern, text_lower):
            found.append(skill)
            seen.add(skill)
    return found


def build_query_from_skills(skills: list[str]) -> str:
    return " ".join(skills)