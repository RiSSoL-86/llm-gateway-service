from services.open_router.parsers.sniffer import AnswerSniffer
from services.open_router.schemas import OpenRouterAnswer


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
