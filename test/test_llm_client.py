import time
import openai
import pytest
from src.ai.llm_client import LLMClient

class DummyResp:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"message": type("Message", (), {"content": content})()})]

class DummyStreamIterable:
    def __init__(self, contents):
        self.contents = contents
    def __iter__(self):
        for content in self.contents:
            time.sleep(0)  # no delay
            chunk = type("Chunk", (), {"choices": [type("Delta", (), {"delta": type("Inner", (), {"content": content})()})]})
            yield chunk

@ pytest.mark.parametrize("model_name", ["gpt-4-turbo", "my-custom-model"])
def test_ask_uses_correct_model(monkeypatch, capsys, model_name):
    client = LLMClient(model=model_name)
    assert client.model == model_name
    called = {}
    def fake_create(model, messages, temperature, max_tokens, stream=False):
        called['model'] = model
        # return dummy response
        return DummyResp("test-response")
    monkeypatch.setattr(openai.chat.completions, 'create', fake_create)
    response = client.ask("recipe", "question")
    out = capsys.readouterr().out
    assert response == "test-response"
    assert called['model'] == model_name
    assert "⏱️ [LLMClient.ask] API call with" in out

@ pytest.mark.parametrize("model_name", ["gpt-4-turbo", "another-model"])
def test_stream_uses_correct_model(monkeypatch, capsys, model_name):
    client = LLMClient(model=model_name)
    assert client.model == model_name
    called = {}
    def fake_create(model, messages, temperature, max_tokens, stream=False):
        called['model'] = model
        assert stream is True
        # return a dummy stream
        return DummyStreamIterable(["X", "Y"])
    monkeypatch.setattr(openai.chat.completions, 'create', fake_create)
    chunks = list(client.stream("recipe", "question"))
    out = capsys.readouterr().out
    assert "XY" == "".join(chunks)
    assert called['model'] == model_name
    assert "⏱️ [LLMClient.stream] total streaming with" in out 