import json
import os

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from ollama import Client
from pydantic import ValidationError

from config import NUM_CTX, OLLAMA_URL, REQUEST_TIMEOUT


def installed_models() -> list[str]:
    client = Client(host=OLLAMA_URL, timeout=3, trust_env=False)
    return sorted(
        item.model for item in client.list().models
        if item.model and not getattr(item, "remote_host", None)
        and not item.model.split(":")[-1].endswith("cloud")
    )


def local_model(name: str) -> ChatOllama:
    return ChatOllama(
        model=name, base_url=OLLAMA_URL, temperature=0,
        num_ctx=NUM_CTX, num_predict=3600, reasoning=False,
        client_kwargs={"timeout": REQUEST_TIMEOUT, "trust_env": False},
    )


def structured_call(prompt, llm, schema, values, validate=None):
    """Constrain Ollama's JSON, parse text with LCEL, and validate with Pydantic."""
    schema_json = schema.model_json_schema()
    options = {}
    if isinstance(llm, ChatOllama):
        small_decision = schema.__name__ in {"Route", "Decision"}
        options["options"] = {
            "num_ctx": NUM_CTX, "temperature": 0,
            "num_predict": 256 if small_decision else 1800,
            "repeat_penalty": 1.08,
        }
    model = llm.bind(format=schema_json, **options)
    chain = prompt | model | StrOutputParser()
    output_spec = (
        "\nReturn one compact JSON object matching this schema. Start with { immediately "
        "and use no blank lines or Markdown.\n"
        + json.dumps(schema_json, ensure_ascii=False, separators=(",", ":"))
    )
    for attempt in range(2):
        raw = chain.invoke({
            **values,
            "format_feedback": output_spec if attempt == 0 else output_spec + "\n" + feedback,
        })
        try:
            result = schema.model_validate_json(raw)
            if validate:
                validate(result)
            return result
        except (ValidationError, ValueError) as exc:
            if isinstance(exc, ValidationError):
                errors = exc.errors(include_input=False, include_context=False, include_url=False)
                feedback = "Correct these output fields: " + "; ".join(
                    f"{'.'.join(map(str, item['loc'])) or 'JSON'}: {item['msg']}"
                    for item in errors[:4]
                )
            else:
                feedback = str(exc)
    raise ValueError(
        f"The local model could not produce valid output. {feedback} "
        "Rephrase the request or try another installed model."
    )
