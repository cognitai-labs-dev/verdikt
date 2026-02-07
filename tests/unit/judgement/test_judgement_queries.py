import pytest

from src.constants import EvaluationType, JudgmentStatus
from src.judgement.queries import JudgementQueries
from tests.factories.judgment import judgment_db_schema_factory

# --- pass_count: LLM_ONLY ---


@pytest.mark.anyio
@pytest.mark.parametrize(
    "passed_1, passed_2, expected",
    [
        pytest.param(False, False, 0, id="none_pass"),
        pytest.param(None, True, 1, id="none_treated_as_not_passing"),
        pytest.param(True, True, 2, id="all_pass"),
    ],
)
async def test_pass_count_for_llm_only(passed_1, passed_2, expected):
    judgments = [
        await judgment_db_schema_factory(passed=passed_1),
        await judgment_db_schema_factory(passed=passed_2),
    ]

    result = JudgementQueries.pass_count(
        EvaluationType.LLM_ONLY, judgments, human=None
    )

    assert result == expected


def test_pass_count_returns_zero_for_empty_list():
    result = JudgementQueries.pass_count(
        EvaluationType.LLM_ONLY, [], human=None
    )

    assert result == 0


# --- pass_count: HUMAN_AND_LLM ---


@pytest.mark.anyio
@pytest.mark.parametrize(
    "human_passed, llm_passed_1, llm_passed_2, expected",
    [
        pytest.param(True, True, False, 1, id="one_match_human_true"),
        pytest.param(True, True, True, 2, id="both_match_human_true"),
        pytest.param(
            False, True, False, 1, id="one_matches_human_false"
        ),
    ],
)
async def test_pass_count_counts_llm_judgments_matching_human(
    human_passed, llm_passed_1, llm_passed_2, expected
):
    human = await judgment_db_schema_factory(passed=human_passed)
    judgments = [
        await judgment_db_schema_factory(passed=llm_passed_1),
        await judgment_db_schema_factory(passed=llm_passed_2),
    ]

    result = JudgementQueries.pass_count(
        EvaluationType.HUMAN_AND_LLM, judgments, human=human
    )

    assert result == expected


@pytest.mark.anyio
async def test_pass_count_returns_zero_when_human_is_none():
    judgments = [await judgment_db_schema_factory(passed=True)]

    result = JudgementQueries.pass_count(
        EvaluationType.HUMAN_AND_LLM, judgments, human=None
    )

    assert result == 0


@pytest.mark.anyio
async def test_pass_count_returns_zero_when_human_passed_is_none():
    human = await judgment_db_schema_factory(passed=None)
    judgments = [await judgment_db_schema_factory(passed=True)]

    result = JudgementQueries.pass_count(
        EvaluationType.HUMAN_AND_LLM, judgments, human=human
    )

    assert result == 0


# --- llm_completion_count ---


@pytest.mark.anyio
@pytest.mark.parametrize(
    "status_1, status_2, expected",
    [
        pytest.param(
            JudgmentStatus.COMPLETED,
            JudgmentStatus.COMPLETED,
            2,
            id="both_completed",
        ),
        pytest.param(
            JudgmentStatus.COMPLETED,
            JudgmentStatus.PENDING,
            1,
            id="one_completed_one_pending",
        ),
        pytest.param(
            JudgmentStatus.PENDING,
            JudgmentStatus.PENDING,
            0,
            id="none_completed",
        ),
    ],
)
async def test_llm_completion_count(status_1, status_2, expected):
    judgments = [
        await judgment_db_schema_factory(status=status_1),
        await judgment_db_schema_factory(status=status_2),
    ]

    result = JudgementQueries.llm_completion_count(judgments)

    assert result == expected


def test_llm_completion_count_returns_zero_for_empty_list():
    result = JudgementQueries.llm_completion_count([])

    assert result == 0


# --- llm_cost ---


@pytest.mark.anyio
@pytest.mark.parametrize(
    "input_cost_1, output_cost_1, input_cost_2, output_cost_2, expected",
    [
        pytest.param(
            0.01, 0.02, 0.03, 0.04, 0.10, id="sums_all_costs"
        ),
        pytest.param(
            None,
            0.05,
            0.03,
            None,
            0.08,
            id="none_costs_treated_as_zero",
        ),
    ],
)
async def test_llm_cost(
    input_cost_1, output_cost_1, input_cost_2, output_cost_2, expected
):
    judgments = [
        await judgment_db_schema_factory(
            input_tokens_cost=input_cost_1,
            output_tokens_cost=output_cost_1,
        ),
        await judgment_db_schema_factory(
            input_tokens_cost=input_cost_2,
            output_tokens_cost=output_cost_2,
        ),
    ]

    result = JudgementQueries.llm_cost(judgments)

    assert result == pytest.approx(expected)


def test_llm_cost_returns_zero_for_empty_list():
    result = JudgementQueries.llm_cost([])

    assert result == 0.0
