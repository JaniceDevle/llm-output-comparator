from src.llm_compare.diff_engine import compare_texts, split_into_chunks


def test_split_into_chunks():
    text = "SQLite is lightweight. It is easy to deploy."
    chunks = split_into_chunks(text)

    assert len(chunks) == 2
    assert chunks[0] == "SQLite is lightweight."


def test_compare_texts_agreement():
    left = "SQLite is lightweight. It is easy to deploy."
    right = "SQLite is lightweight. It can be deployed easily."

    result = compare_texts(left, right)

    assert result.agreement_score > 0.4
    assert len(result.left_segments) == 2
    assert len(result.right_segments) == 2


def test_compare_texts_difference():
    left = "SQLite is good for small applications."
    right = "PostgreSQL is better for high-concurrency systems."

    result = compare_texts(left, right)

    assert result.agreement_score < 0.7