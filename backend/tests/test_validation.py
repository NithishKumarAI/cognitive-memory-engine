import pytest
from pydantic import ValidationError

from app.schemas.learning_track import LearningTrackCreate, LearningTrackUpdate
from app.schemas.study_logs import StudyLogCreate, StudyLogUpdate
from app.schemas.memory import MemoryCreate, MemoryUpdate


@pytest.mark.parametrize("schema,base,field", [
    (LearningTrackCreate, {"name": "Title"}, "name"),
    (MemoryCreate, {"title": "Title", "content": "Text", "category": "test"}, "title"),
    (MemoryCreate, {"title": "Title", "content": "Text", "category": "test"}, "content"),
    (StudyLogCreate, {"topic": "Topic", "duration_minutes": 1, "notes": ""}, "topic"),
    (LearningTrackUpdate, {}, "name"), (MemoryUpdate, {}, "title"),
    (MemoryUpdate, {}, "content"), (StudyLogUpdate, {}, "topic"),
])
@pytest.mark.parametrize("value", ["", " \t\n", None])
def test_required_text(schema, base, field, value):
    with pytest.raises(ValidationError):
        schema(**{**base, field: value})


@pytest.mark.parametrize("schema,base", [(StudyLogCreate, {"topic": "Topic", "notes": ""}), (StudyLogUpdate, {})])
@pytest.mark.parametrize("value", [-1, 0, None])
def test_duration(schema, base, value):
    with pytest.raises(ValidationError):
        schema(**base, duration_minutes=value)


@pytest.mark.parametrize("schema,field", [(MemoryUpdate, "category"), (StudyLogUpdate, "notes")])
def test_nonnullable_update(schema, field):
    with pytest.raises(ValidationError):
        schema(**{field: None})


@pytest.mark.parametrize("schema", [LearningTrackUpdate, StudyLogUpdate, MemoryUpdate])
def test_partial_updates(schema):
    assert schema().model_dump(exclude_unset=True) == {}


@pytest.mark.parametrize("schema,field", [(MemoryUpdate, "study_log_id"), (StudyLogUpdate, "learning_track_id"), (LearningTrackUpdate, "description")])
def test_nullable_unlink(schema, field):
    assert schema(**{field: None}).model_dump(exclude_unset=True) == {field: None}
