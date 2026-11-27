from services.open_router.constants import LARGE_ANSWER_BYTES
from services.open_router.parsers.sniffer import AnswerSniffer
from services.open_router.schemas import OpenRouterAnswer


def test_keeps_responses_stream_error() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)

    sniffer.feed(
        chunk=b'data: {"type":"error","code":"server_error",'
        b'"message":"Provider failed"}\n\n'
    )

    assert answer.error == "Provider failed"


def test_finds_usage_split_across_chunks() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)

    sniffer.feed(chunk=b": keep-alive\n\n")
    assert not answer.seen_data
    sniffer.feed(chunk=b'data: {"id":"g","choices":[]}\n\ndata: {"usa')
    sniffer.feed(chunk=b'ge":{"total_tokens":3}}\n\ndata: [DONE]\n\n')
    sniffer.finish()

    assert answer.seen_data
    assert answer.generation_id == "g"
    assert answer.usage == {"total_tokens": 3}


def test_finds_mid_stream_error_without_newline() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)

    sniffer.feed(
        chunk=b'data: {"id":"g"}\n\ndata: {"error":{"message":"boom"}}'
    )
    sniffer.finish()

    assert answer.error == "boom"


def test_ignores_quoted_words_in_content() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)

    sniffer.feed(chunk=b'data: {"id":"g"}\n\n')
    sniffer.feed(
        chunk=b'data: {"choices":[{"delta":{"content":"\\"usage\\""}}]}\n'
    )

    assert answer.usage is None


def test_first_token_skips_role_only_delta() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)

    sniffer.feed(
        chunk=b'data: {"choices":[{"delta":{"role":"assistant"}}]}\n\n'
    )
    assert answer.seen_data
    assert not answer.seen_token
    sniffer.feed(chunk=b'data: {"choices":[{"delta":{"content":"Hi"}}]}\n\n')

    assert answer.seen_token


def test_keeps_error_without_message() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)

    sniffer.inspect_json(payload=b'{"error":{"code":502}}')

    assert answer.error == '{"code": 502}'


def test_first_token_of_text_completion() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)

    sniffer.feed(chunk=b'data: {"choices":[{"text":""}]}\n\n')
    assert not answer.seen_token
    sniffer.feed(chunk=b'data: {"choices":[{"text":"Hi"}]}\n\n')

    assert answer.seen_token


def test_reads_long_line_fed_in_pieces() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)
    line = b'data: {"id":"g","choices":[{"delta":{"content":"' + b"x" * 1000

    for start in range(0, len(line), 7):
        sniffer.feed(chunk=line[start : start + 7])
    sniffer.feed(chunk=b'"}}]}\n\n')

    assert answer.generation_id == "g"
    assert answer.seen_token


def test_reads_own_fields_of_large_answer() -> None:
    answer = OpenRouterAnswer()
    sniffer = AnswerSniffer(answer=answer)
    vector = b"[" + b",".join([b"0.0123456789"] * 1000) + b"]"
    item = b'{"object":"embedding","embedding":' + vector + b',"index":0}'
    data = b",".join([item] * 100)
    payload = (
        b'{"object":"list","data":[' + data + b'],"model":"e",'
        b'"id":"gen-5","provider":"P",'
        b'"usage":{"prompt_tokens":7,"cost":0.1}}'
    )
    assert len(payload) > LARGE_ANSWER_BYTES

    sniffer.inspect_json(payload=payload)

    assert answer.generation_id == "gen-5"
    assert answer.model == "e"
    assert answer.provider == "P"
    assert answer.usage == {"prompt_tokens": 7, "cost": 0.1}
