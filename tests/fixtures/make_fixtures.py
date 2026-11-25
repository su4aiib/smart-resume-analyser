"""Generate fictional resume fixtures. Run once: python tests/fixtures/make_fixtures.py

All names, emails and phone numbers are fictional.
"""

from __future__ import annotations

from pathlib import Path

import docx
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

FIXTURES = Path(__file__).resolve().parent

STRONG_RESUME = """Jane Doe
jane.doe@example.com | +1 555-010-2345 | Springfield

Summary
Backend engineer with 5 years of experience building Python and Java services on AWS.
Focused on REST APIs, PostgreSQL performance and CI/CD automation. Comfortable leading
small teams and mentoring junior developers through code reviews and design discussions.

Skills
Python, Java, JavaScript, SQL, FastAPI, Django, Docker, Kubernetes, AWS, PostgreSQL,
Redis, Git, Jenkins, Terraform, React, Communication, Teamwork, Problem Solving

Experience
Backend Engineer, Example Corp (2021 - Present)
- Led migration of 12 services to Kubernetes, reducing deployment time by 40%.
- Built REST APIs in Python and FastAPI serving 2 million requests per day.
- Improved PostgreSQL query performance, cutting p95 latency by 35%.
- Mentored 3 junior engineers on testing and code review practices.
- Automated infrastructure with Terraform across 4 AWS accounts.
- Implemented Redis caching that lowered database load by 25%.

Software Developer, Sample Labs (2019 - 2021)
- Developed Java microservices and a React dashboard used by 300 internal users.
- Maintained Jenkins CI pipelines with a 95% build success rate.
- Designed unit and integration tests, raising coverage from 60% to 85%.
- Collaborated with product managers to deliver 10 features across 3 quarterly releases.

Education
B.Sc. Computer Science, State University, 2019

Projects
Resume tracker: Django application with Docker deployment, used by 500 beta users each month.
Inventory API: FastAPI service with automated test suite and GitHub Actions pipeline.

Certifications
AWS Certified Developer - Associate (2022)
"""

WEAK_RESUME = """John Smith
I like computers and want a job.

Experience
Helped at a store.
Did some work on the computer.

Skills
Computers
"""


def write_docx(path: Path, text: str) -> None:
    document = docx.Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    document.save(path)


def write_pdf(path: Path, text: str) -> None:
    styles = getSampleStyleSheet()
    story = []
    for line in text.splitlines():
        if line.strip():
            story.append(Paragraph(line.replace("&", "and"), styles["BodyText"]))
        else:
            story.append(Spacer(1, 6))
    SimpleDocTemplate(str(path), pagesize=A4).build(story)


def write_blank_pdf(path: Path) -> None:
    SimpleDocTemplate(str(path), pagesize=A4).build([Spacer(1, 10)])


def main() -> None:
    write_docx(FIXTURES / "strong_resume.docx", STRONG_RESUME)
    write_pdf(FIXTURES / "strong_resume.pdf", STRONG_RESUME)
    write_docx(FIXTURES / "weak_resume.docx", WEAK_RESUME)
    write_blank_pdf(FIXTURES / "blank_scanned.pdf")
    (FIXTURES / "sample_job_description.txt").write_text(
        "Backend Engineer\nWe need a Python developer with FastAPI, PostgreSQL, Docker and "
        "Kubernetes experience. Knowledge of AWS and Terraform is a plus. Strong communication "
        "skills and teamwork are valued.\n",
        encoding="utf-8",
    )
    print("Fixtures written to", FIXTURES)


if __name__ == "__main__":
    main()
