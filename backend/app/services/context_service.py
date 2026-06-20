from app.models.memory import Memory


class ContextService:

    @staticmethod
    def build_memory_context(
        memories: list[Memory]
    ) -> str:

        if not memories:
            return "No relevant memories found."

        context_parts = []

        for index, memory in enumerate(memories, start=1):

            context_parts.append(
                f"""
Memory {index}
Title: {memory.title}
Category: {memory.category}

Content:
{memory.content}
"""
            )

        return "\n\n".join(context_parts)


context_service = ContextService()