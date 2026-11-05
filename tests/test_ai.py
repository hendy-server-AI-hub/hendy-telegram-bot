from app.services.ai import extract_response_text


def test_extracts_text_from_responses_api():
    payload = {
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": "Hendy ready"}]},
        ]
    }
    assert extract_response_text(payload) == "Hendy ready"
