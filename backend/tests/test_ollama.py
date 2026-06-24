from app.services.ollama import OllamaService


def test_qwen_model_routing_prefers_exact_local_tags():
    models = ["qwen2.5-coder:14b", "qwen2.5-coder:7b"]
    assert OllamaService._resolve("qwen2.5-coder:7b", models) == "qwen2.5-coder:7b"
    assert OllamaService._resolve("qwen2.5-coder:14b", models) == "qwen2.5-coder:14b"


def test_qwen_model_routing_falls_back_by_model_family():
    assert OllamaService._resolve("qwen2.5-coder:latest", ["qwen2.5-coder:7b"]) == "qwen2.5-coder:7b"
