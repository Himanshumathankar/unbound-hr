import re

from unbound_hr.services.resume_processing import (
    COMMON_SKILLS,
    extract_education_signals,
    extract_skills,
    normalize_text,
)


def percentage(matched, total):
    if total <= 0:
        return 0.0

    return round(
        min(100.0, (matched / total) * 100),
        2,
    )


def extract_required_experience(jd_text):
    text = normalize_text(jd_text)

    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s+years?",
        r"minimum\s+(\d+(?:\.\d+)?)\+?\s+years?",
        r"(\d+(?:\.\d+)?)\+?\s+years?\s+of\s+experience",
        r"(\d+(?:\.\d+)?)\+?\s+years?\s+experience",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if not match:
            continue

        numbers = [
            float(value)
            for value in match.groups()
            if value is not None
        ]

        if numbers:
            return min(numbers)

    return 0.0


def score_skills(candidate_skills, jd_text):
    jd_skills = extract_skills(jd_text)

    if not jd_skills:
        return {
            "score": 0.0,
            "matched": [],
            "missing": [],
            "jd_skills": [],
        }

    candidate_set = set(candidate_skills)
    jd_set = set(jd_skills)

    matched = sorted(candidate_set & jd_set)
    missing = sorted(jd_set - candidate_set)

    return {
        "score": percentage(
            len(matched),
            len(jd_set),
        ),
        "matched": matched,
        "missing": missing,
        "jd_skills": sorted(jd_set),
    }


def score_experience(candidate_years, jd_text):
    required = extract_required_experience(jd_text)

    if required <= 0:
        return {
            "score": 0.0,
            "candidate_years": candidate_years,
            "required_years": 0.0,
        }

    score = min(
        100.0,
        (candidate_years / required) * 100,
    )

    return {
        "score": round(score, 2),
        "candidate_years": candidate_years,
        "required_years": required,
    }


def education_level_value(level):
    mapping = {
        "diploma": 1,
        "bachelors": 2,
        "masters": 3,
        "phd": 4,
    }

    return mapping.get(level, 0)


def highest_education(signals):
    if not signals:
        return None

    return max(
        signals,
        key=education_level_value,
    )


def score_education(candidate_education, jd_text):
    jd_education = extract_education_signals(jd_text)

    candidate_level = highest_education(
        candidate_education
    )

    required_level = highest_education(
        jd_education
    )

    if not required_level:
        return {
            "score": 0.0,
            "candidate_level": candidate_level,
            "required_level": None,
        }

    candidate_value = education_level_value(
        candidate_level
    )

    required_value = education_level_value(
        required_level
    )

    if candidate_value >= required_value:
        score = 100.0
    elif candidate_value > 0:
        score = round(
            (candidate_value / required_value) * 100,
            2,
        )
    else:
        score = 0.0

    return {
        "score": score,
        "candidate_level": candidate_level,
        "required_level": required_level,
    }


def calculate_match(candidate, jd_text):
    skills = score_skills(
        candidate["skills"],
        jd_text,
    )

    experience = score_experience(
        candidate["years_experience"],
        jd_text,
    )

    education = score_education(
        candidate["education"],
        jd_text,
    )

    ats_score = round(
        skills["score"] * 0.50
        + experience["score"] * 0.30
        + education["score"] * 0.20,
        2,
    )

    return {
        "ats_score": ats_score,
        "skills": skills,
        "experience": experience,
        "education": education,
    }
