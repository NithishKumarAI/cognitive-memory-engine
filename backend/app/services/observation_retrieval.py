"""Bounded literal recall over owned confirmed history, independent of record age."""
import re
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session
from app.models.learning_capture import LearningCapture, LearningObservation

MAX_TERMS = 8
MAX_OBSERVATIONS = 5
MAX_BODY_CHARS = 2000
MAX_EVIDENCE_CHARS = 400
STOP_WORDS = frozenset("a an and are as at be been by can could did do does for from had has have how i in into is it me my of on or our please about explain describe tell recorded record records learn learned learning study studied studying what when where which who why with was were will would should you your the this that these those ago months month years year days day last time recently recent stop stopped leave left off thing say report reported understood struggling difficulties difficulty confused difficult next steps step practice plan planned questions question open unanswered".split())


def recall_terms(question: str) -> tuple[str, ...]:
    terms = []
    for word in re.findall(r"[^\W_]+(?:\+\+|#)?", question.lower()):
        if len(word) < 2 or len(word) > 64 or word.isdecimal() or word in STOP_WORDS or word in terms:
            continue
        terms.append(word)
        if len(terms) == MAX_TERMS:
            break
    return tuple(terms)


def literal_word_pattern(term: str) -> str:
    return r"(?i)(^|[^\w])" + re.escape(term) + r"($|[^\w])"


def topic_matches_terms(topic: str, terms: tuple[str, ...]) -> bool:
    return any(re.search(literal_word_pattern(term), topic) for term in terms)


def search_confirmed_observations(db: Session, user_id: int, question: str):
    terms = recall_terms(question)
    if not terms:
        return []
    topic_matches, content_matches = [], []
    for term in terms:
        pattern = literal_word_pattern(term)
        topic_matches.append(LearningObservation.topic.regexp_match(pattern))
        content_matches.append(LearningObservation.content.regexp_match(pattern))
    coverage = sum(case((or_(topic, content), 1), else_=0) for topic, content in zip(topic_matches, content_matches))
    topic_score = sum(case((match, 1), else_=0) for match in topic_matches)
    content_score = sum(case((match, 1), else_=0) for match in content_matches)
    # SQL filters and ranks all eligible ages before LIMIT. Only bounded projections cross into Python.
    return db.query(LearningObservation.id, LearningObservation.capture_id,
        func.substr(LearningObservation.topic, 1, 200).label("topic"), LearningObservation.observation_type,
        func.substr(LearningObservation.content, 1, MAX_BODY_CHARS).label("content"),
        func.substr(LearningObservation.evidence, 1, MAX_EVIDENCE_CHARS).label("evidence")).join(
        LearningCapture, LearningCapture.id == LearningObservation.capture_id).filter(
        LearningObservation.user_id == user_id, LearningCapture.user_id == user_id,
        LearningCapture.status == "confirmed", or_(*(topic_matches + content_matches))).order_by(
        coverage.desc(), topic_score.desc(), content_score.desc(),
        func.coalesce(LearningCapture.confirmed_at, LearningCapture.created_at).desc(), LearningObservation.id.desc()
    ).limit(MAX_OBSERVATIONS).all()
