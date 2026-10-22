from app.models.memory import Memory


class ContextService:

    @staticmethod
    def build_memory_context(
        memories: list[Memory]
    ) -> str:

        if not memories:
            return "No relevant memories found."

        context_parts = []

        for memory in memories:

            context_parts.append(
                f"""
Memory {memory.id}
Title: {memory.title}
Category: {memory.category}

Content:
{memory.content}
"""
            )

        return "\n\n".join(context_parts)


context_service = ContextService()