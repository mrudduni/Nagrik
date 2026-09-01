"""
LangGraph checkpointer factory. Start with in-memory for local dev,
swap to Redis/Postgres for anything that needs to survive a restart
(and for the actual hackathon deployment).
"""
from app.config import settings


def get_checkpointer():
    backend = settings.checkpointer_backend

    if backend == "memory":
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

    if backend == "redis":
        # Requires: pip install langgraph-checkpoint-redis
        try:
            from langgraph.checkpoint.redis import RedisSaver
        except ImportError as e:
            raise ImportError(
                "Redis checkpointer selected but langgraph-checkpoint-redis "
                "is not installed. `pip install langgraph-checkpoint-redis`"
            ) from e
        return RedisSaver.from_conn_string(settings.redis_url)

    if backend == "postgres":
        # Requires: pip install langgraph-checkpoint-postgres
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as e:
            raise ImportError(
                "Postgres checkpointer selected but langgraph-checkpoint-postgres "
                "is not installed. `pip install langgraph-checkpoint-postgres`"
            ) from e
        return PostgresSaver.from_conn_string(settings.postgres_dsn)

    raise ValueError(f"Unknown CHECKPOINTER_BACKEND '{backend}'")
