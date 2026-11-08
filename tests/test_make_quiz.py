"""Day3: make_quiz の動作とエージェントへの登録を検証する。"""

from pydantic_ai.models.test import TestModel

from app.agent import agent
from app.tools import load_glossary, make_quiz


def test_make_quiz_lecture_two():
    result = make_quiz(2)
    terms = [e for e in load_glossary() if e["lecture"] == 2]

    assert result.startswith("問題: ")
    assert "模範解答: " in result
    assert any(
        e["term"] in result and e["definition"] in result
        for e in terms
    )


def test_make_quiz_unknown_lecture():
    result = make_quiz(999)
    assert "見つかりませんでした" in result


def test_make_quiz_registered():
    model = TestModel(call_tools=[])

    with agent.override(model=model):
        agent.run_sync("確認問題を出して")

    offered = {
        tool.name
        for tool in model.last_model_request_parameters.function_tools
    }

    assert "make_quiz" in offered
