"""Container entrypoint; does not initialize models or run migrations."""
import os


def configured_port(value=None):
    raw = os.environ.get("PORT", "8000") if value is None else value
    if not raw.isascii() or not raw.isdecimal() or not 1 <= int(raw) <= 65535:
        raise ValueError("PORT must be an integer between 1 and 65535")
    return int(raw)


def main():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=configured_port())


if __name__ == "__main__":
    main()
