import pytest
from sqlalchemy import delete

from app.models.learning_track import LearningTrack
from app.models.study_log import StudyLog
from app.models.memory import Memory
from app.crud.learning_track import delete_learning_track


@pytest.mark.parametrize("mode", ["orm_loaded", "orm_unloaded", "database"])
def test_track_deletion_preserves_history(db, users, mode):
    track = LearningTrack(user_id=users[0].id, name="Track")
    other = LearningTrack(user_id=users[1].id, name="Other")
    db.add_all([track, other])
    db.flush()
    logs = [StudyLog(user_id=users[0].id, learning_track_id=track.id,
                     topic="Topic", duration_minutes=10, notes="") for _ in range(2)]
    other_log = StudyLog(user_id=users[1].id, learning_track_id=other.id,
                         topic="Other", duration_minutes=5, notes="")
    db.add_all([*logs, other_log])
    db.flush()
    memory = Memory(user_id=users[0].id, study_log_id=logs[0].id,
                    title="Memory", content="Text", category="test")
    db.add(memory)
    db.commit()
    track_id, log_ids, memory_id, other_id = track.id, [log.id for log in logs], memory.id, other.id
    if mode == "orm_loaded":
        assert len(track.study_logs) == 2
    if mode == "database":
        db.execute(delete(LearningTrack).where(LearningTrack.id == track_id))
        db.commit()
    else:
        delete_learning_track(db, track)
    db.expire_all()
    assert db.get(LearningTrack, track_id) is None
    for log_id in log_ids:
        assert db.get(StudyLog, log_id).learning_track_id is None
    assert db.get(Memory, memory_id).study_log_id == log_ids[0]
    assert db.get(StudyLog, other_log.id).learning_track_id == other_id
    assert db.get(LearningTrack, other_id).user_id == users[1].id
