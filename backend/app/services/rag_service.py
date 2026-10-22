import re
from math import isfinite
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud.retrieval import search_memories_by_embedding
from app.services.embedding_service import generate_embedding
from app.services.context_service import context_service
from app.services.llm_service import llm_service
from app.crud.conversation import create_conversation
from app.models.learning_capture import LearningCapture, LearningObservation
from app.services.continuity_service import (
    get_resumable_checkpoints,
    get_user_actions,
    generate_evidence_recommendations,
    normalize_topic,
)


class RAGService:

    def _match_deterministic_continuity(self, db: Session, user_id: int, question: str):
        q = question.strip().lower()

        # 1. "where did i stop" / "where did i leave off" / "what was the last thing i studied"
        is_checkpoint_q = bool(re.search(r"\b(where did i (stop|leave off)|what was the last thing i studied|what have i been learning)\b", q))

        # 2. "what was i struggling with" / "what difficulties did i record" / "what confused me"
        is_diff_q = bool(re.search(r"\b(struggling with|difficulties|what confused me|what was difficult)\b", q))

        # 3. "what should i practice next" / "what should i study next" / "what were my next steps" / "what did i plan"
        is_next_q = bool(re.search(r"\b(what should i (practice|study) next|next steps?|what did i plan)\b", q))

        # 4. "what questions did i leave unanswered" / "what open questions"
        is_open_q = bool(re.search(r"\b(questions did i leave|open questions|unanswered questions)\b", q))

        # 5. "did i say i understood"
        understood_match = re.search(r"\bdid i (say|report) i understood\s+([a-zA-Z0-9_\s]+)", q)

        if not (is_checkpoint_q or is_diff_q or is_next_q or is_open_q or understood_match):
            return None

        # Guard against mock DBs in unit tests
        try:
            checkpoints = get_resumable_checkpoints(db, user_id, limit=20)
        except Exception:
            return None

        if is_checkpoint_q:
            matched_cp = None
            for cp in checkpoints:
                if cp.normalized_topic and cp.normalized_topic in q:
                    matched_cp = cp
                    break
            if not matched_cp and checkpoints:
                matched_cp = checkpoints[0]

            if not matched_cp:
                return {
                    "answer": "You have not recorded any confirmed learning updates yet.",
                    "sources": [],
                }

            last_date_str = (
                matched_cp.last_capture_at.strftime("%Y-%m-%d")
                if matched_cp.last_capture_at
                else "recently"
            )
            cap_id = matched_cp.last_capture_id or "N/A"
            obs_content = matched_cp.latest_observation_content or matched_cp.last_capture_excerpt or ""
            answer = (
                f"Your last recorded learning about '{matched_cp.topic}' was in Capture #{cap_id} on {last_date_str}. "
                f"Your latest recorded observation was: '{obs_content}'."
            )
            sources = []
            if matched_cp.latest_observation_id:
                sources.append({
                    "source_type": "observation",
                    "memory_id": None,
                    "observation_id": matched_cp.latest_observation_id,
                    "capture_id": matched_cp.latest_observation_capture_id or matched_cp.last_capture_id,
                    "title": f"Observation: {matched_cp.topic}",
                    "category": "learning_checkpoint",
                    "distance": 0.0,
                    "evidence": obs_content,
                })
            return {"answer": answer, "sources": sources}

        if is_diff_q:
            unresolved = []
            for cp in checkpoints:
                unresolved.extend(cp.unresolved_difficulties)

            if not unresolved:
                return {
                    "answer": "You currently have no unresolved difficulties recorded in your confirmed learning updates.",
                    "sources": [],
                }

            items_text = []
            sources = []
            for d in unresolved[:5]:
                items_text.append(f"- {d.topic}: \"{d.content}\" (Capture #{d.capture_id})")
                sources.append({
                    "source_type": "observation",
                    "memory_id": None,
                    "observation_id": d.id,
                    "capture_id": d.capture_id,
                    "title": f"Difficulty: {d.topic}",
                    "category": "difficulty",
                    "distance": 0.0,
                    "evidence": d.evidence,
                })

            answer = "You previously reported the following difficulties:\n" + "\n".join(items_text)
            return {"answer": answer, "sources": sources}

        if is_next_q:
            pending_steps = []
            for cp in checkpoints:
                pending_steps.extend(cp.pending_next_steps)

            if pending_steps:
                items_text = []
                sources = []
                for s in pending_steps[:5]:
                    items_text.append(f"- {s.topic}: \"{s.content}\" (Capture #{s.capture_id})")
                    sources.append({
                        "source_type": "observation",
                        "memory_id": None,
                        "observation_id": s.id,
                        "capture_id": s.capture_id,
                        "title": f"Next step: {s.topic}",
                        "category": "intended_next_step",
                        "distance": 0.0,
                        "evidence": s.evidence,
                    })
                answer = "Based on your confirmed intended next steps, you planned to:\n" + "\n".join(items_text)
                return {"answer": answer, "sources": sources}

            try:
                recs = generate_evidence_recommendations(db, user_id, limit=1)
            except Exception:
                recs = []

            if recs:
                top_rec = recs[0]
                answer = f"Based on your learning continuity, it is recommended to: {top_rec.action}. Reason: {top_rec.reason}."
                sources = []
                if top_rec.source_observation_id:
                    sources.append({
                        "source_type": "observation",
                        "memory_id": None,
                        "observation_id": top_rec.source_observation_id,
                        "capture_id": top_rec.source_capture_id,
                        "title": f"Recommendation: {top_rec.topic}",
                        "category": top_rec.type,
                        "distance": 0.0,
                        "evidence": top_rec.evidence,
                    })
                return {"answer": answer, "sources": sources}

            return {
                "answer": "You have no pending next steps or study plans recorded.",
                "sources": [],
            }

        if is_open_q:
            unresolved_q = []
            for cp in checkpoints:
                unresolved_q.extend(cp.unresolved_questions)

            if not unresolved_q:
                return {
                    "answer": "You have no open questions recorded in your confirmed learning updates.",
                    "sources": [],
                }

            items_text = []
            sources = []
            for oq in unresolved_q[:5]:
                items_text.append(f"- {oq.topic}: \"{oq.content}\" (Capture #{oq.capture_id})")
                sources.append({
                    "source_type": "observation",
                    "memory_id": None,
                    "observation_id": oq.id,
                    "capture_id": oq.capture_id,
                    "title": f"Question: {oq.topic}",
                    "category": "open_question",
                    "distance": 0.0,
                    "evidence": oq.evidence,
                })
            answer = "You recorded the following open question(s):\n" + "\n".join(items_text)
            return {"answer": answer, "sources": sources}

        if understood_match:
            topic_query = normalize_topic(understood_match.group(2).strip().rstrip("?"))
            try:
                understood_obs = (
                    db.query(LearningObservation)
                    .join(LearningCapture, LearningObservation.capture_id == LearningCapture.id)
                    .filter(
                        LearningObservation.user_id == user_id,
                        LearningCapture.status == "confirmed",
                        LearningObservation.observation_type == "understood_self_report",
                        func.lower(LearningObservation.topic).contains(topic_query),
                    )
                    .order_by(LearningObservation.created_at.desc())
                    .first()
                )
            except Exception:
                understood_obs = None

            if understood_obs:
                dt_str = understood_obs.created_at.strftime("%Y-%m-%d")
                answer = (
                    f"Yes. In Capture #{understood_obs.capture_id} on {dt_str}, you self-reported understanding: "
                    f"\"{understood_obs.content}\" regarding '{understood_obs.topic}'. "
                    f"Note that this represents your self-report, not verified subject mastery."
                )
                sources = [{
                    "source_type": "observation",
                    "memory_id": None,
                    "observation_id": understood_obs.id,
                    "capture_id": understood_obs.capture_id,
                    "title": f"Understood: {understood_obs.topic}",
                    "category": "understood_self_report",
                    "distance": 0.0,
                    "evidence": understood_obs.evidence,
                }]
                return {"answer": answer, "sources": sources}
            else:
                return {
                    "answer": f"You have not recorded a self-report of understanding for '{topic_query}'.",
                    "sources": [],
                }

        return None

    def generate_answer(
        self,
        db: Session,
        user_id: int,
        question: str,
        top_k: int = 5
    ):
        # 1. Deterministic continuity handler for direct continuity queries
        deterministic = self._match_deterministic_continuity(db, user_id, question)
        if deterministic is not None:
            try:
                db.rollback()
            except Exception:
                pass
            create_conversation(
                db=db,
                user_id=user_id,
                message=question,
                response=deterministic["answer"]
            )
            return deterministic

        # 2. General RAG retrieval: check memory embeddings
        query_embedding = generate_embedding(question)

        try:
            retrieval_results = search_memories_by_embedding(
                db=db,
                user_id=user_id,
                query_embedding=query_embedding,
                limit=top_k
            )
        except Exception:
            retrieval_results = []

        # Nearest does not imply relevant; reject distant/nonfinite candidates.
        retrieval_results = [(memory, distance) for memory, distance in retrieval_results
                             if isfinite(float(distance)) and float(distance) <= 0.5]
        memories = [memory for memory, _distance in retrieval_results]

        # 3. Retrieve confirmed learning observations matching keywords
        keywords = [w for w in re.split(r"\W+", question.lower()) if len(w) > 3]
        matched_observations = []
        if keywords:
            try:
                obs_query = (
                    db.query(LearningObservation)
                    .join(LearningCapture, LearningObservation.capture_id == LearningCapture.id)
                    .filter(
                        LearningObservation.user_id == user_id,
                        LearningCapture.status == "confirmed",
                    )
                )
                candidate_obs = obs_query.order_by(LearningObservation.id.desc()).limit(30).all()
                if isinstance(candidate_obs, (list, tuple)):
                    for obs in candidate_obs:
                        obs_text = f"{obs.topic} {obs.content}".lower()
                        if any(kw in obs_text for kw in keywords):
                            matched_observations.append(obs)
                            if len(matched_observations) >= 5:
                                break
            except Exception:
                matched_observations = []

        context_parts = []
        if memories:
            memory_context = context_service.build_memory_context(memories)
            context_parts.append(f"MEMORIES:\n\n{memory_context}")

        if matched_observations:
            obs_lines = []
            for obs in matched_observations:
                obs_lines.append(
                    f"[Observation {obs.id}] (Capture #{obs.capture_id}, Topic: {obs.topic}, Type: {obs.observation_type}):\n"
                    f"{obs.content}\nEvidence excerpt: {obs.evidence}"
                )
            context_parts.append("CONFIRMED LEARNING OBSERVATIONS:\n\n" + "\n\n".join(obs_lines))

        full_context = "\n\n".join(context_parts)

        prompt = f"""
You are a personal cognitive memory assistant.

Answer the user's question using ONLY the provided memories.

When you use information from a memory,
cite it using the format:

[Memory X]

where X is the actual database memory ID shown below (for example [Memory 13]).
Only cite memories whose information you actually use.

When you use information from a confirmed learning observation,
cite it using the format:

[Observation Y]

where Y is the actual database observation ID shown below.

If the memories do not contain enough information,
say that the information is not available in memory.

{full_context}

USER QUESTION:

{question}
"""

        sources = []
        for memory, distance in retrieval_results:
            sources.append(
                {
                    "source_type": "memory",
                    "memory_id": memory.id,
                    "observation_id": None,
                    "capture_id": None,
                    "title": memory.title,
                    "category": memory.category,
                    "distance": float(distance),
                    "evidence": None,
                }
            )

        for obs in matched_observations:
            sources.append(
                {
                    "source_type": "observation",
                    "memory_id": None,
                    "observation_id": obs.id,
                    "capture_id": obs.capture_id,
                    "title": f"Observation: {obs.topic}",
                    "category": obs.observation_type,
                    "distance": 0.0,
                    "evidence": obs.evidence,
                }
            )

        try:
            db.rollback()  # Release retrieval transaction before external LLM call.
        except Exception:
            pass

        has_data = bool(memories or matched_observations)
        answer = (
            llm_service.generate_response(prompt)
            if has_data else "The information is not available in memory."
        )

        create_conversation(
            db=db,
            user_id=user_id,
            message=question,
            response=answer
        )

        return {
            "answer": answer,
            "sources": sources
        }


rag_service = RAGService()
