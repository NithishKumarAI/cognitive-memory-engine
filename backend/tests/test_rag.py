from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.services import rag_service as module
from app.services.context_service import context_service


@pytest.mark.parametrize("empty", [False, True])
def test_real_ids_and_empty_results(monkeypatch, empty):
    memories = [SimpleNamespace(id=i, title=f"Title {i}", content="Text", category="test") for i in (13, 42)]
    retrieval = Mock(return_value=[] if empty else [(m, 0.1) for m in memories])
    monkeypatch.setattr(module, "search_memories_by_embedding", retrieval)
    monkeypatch.setattr(module, "generate_embedding", Mock(return_value=[0.1] * 768))
    llm = Mock(return_value="Answer from [Memory 42]")
    monkeypatch.setattr(module.llm_service, "generate_response", llm)
    conversation = Mock()
    monkeypatch.setattr(module, "create_conversation", conversation)
    result = module.rag_service.generate_answer(object(), 7, "Question")
    assert retrieval.call_args.kwargs["user_id"] == 7
    conversation.assert_called_once()
    if empty:
        llm.assert_not_called()
        assert result == {"answer": "The information is not available in memory.", "sources": []}
        assert context_service.build_memory_context([]) == "No relevant memories found."
    else:
        prompt = llm.call_args.args[0]
        assert "Memory 13\n" in prompt and "Memory 42\n" in prompt
        assert "Memory 1\n" not in prompt
        assert "actual database memory ID" in prompt
        # Sources retain retrieved candidates; they do not assert citation use.
        assert [source["memory_id"] for source in result["sources"]] == [13, 42]
        assert result["answer"] == "Answer from [Memory 42]"
