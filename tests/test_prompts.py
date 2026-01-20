"""Tests for prompt builders."""

import pytest

from src.api.models import (
    CompilerError,
    Constraints,
    ContextPack,
    ConversationSummary,
    RetrievedChunk,
)
from src.prompts.codegen_spec import build_codegen_prompt_spec
from src.prompts.repair_spec import build_repair_prompt_spec


@pytest.fixture
def basic_context_pack():
    """Create a basic context pack for testing."""
    return ContextPack(
        latest_ask="Create a function that adds two numbers",
        current_code=None,
        conversation_summary=None,
        retrieved_chunks=[],
        constraints=Constraints(dialect="0002"),
        task_type="codegen",
    )


@pytest.fixture
def full_context_pack():
    """Create a full context pack with all fields populated."""
    return ContextPack(
        latest_ask="Update the table with new headers",
        current_code='let table = [["A" "B"]]..',
        conversation_summary=ConversationSummary(
            turn_count=3,
            previous_requests=["Create a table", "Add headers"],
            previous_outputs=["[Generated code]", "[Generated code]"],
        ),
        retrieved_chunks=[
            RetrievedChunk(
                id="ex-1",
                prompt="Create headers",
                code='let headers = ["X" "Y"]..',
                similarity=0.9,
            ),
            RetrievedChunk(
                id="ex-2",
                prompt="Build a table",
                code="let table = []..",
                similarity=0.85,
            ),
        ],
        constraints=Constraints(
            dialect="0165",
            allowed_builtins=["map", "filter"],
            max_output_tokens=2048,
        ),
        task_type="codegen",
    )


@pytest.fixture
def repair_context_pack():
    """Create a context pack for repair testing."""
    return ContextPack(
        latest_ask="Create a doubling function",
        current_code=None,
        conversation_summary=None,
        retrieved_chunks=[],
        constraints=Constraints(dialect="0002"),
        task_type="repair",
        last_model_output="let double = <x: mul x 2>",
        structured_compiler_errors=[
            CompilerError(
                type="syntax",
                message="Expected '..' at end of let statement",
                line=1,
                column=28,
            )
        ],
    )


class TestCodegenSpec:
    """Tests for code generation prompt spec builder."""

    def test_build_basic_spec(self, basic_context_pack):
        """Test building a basic codegen spec."""
        spec = build_codegen_prompt_spec(basic_context_pack)

        assert spec.version == "1.0.0"
        assert spec.spec_id.startswith("ps_")
        assert len(spec.spec_id) > 3
        assert "L0002" in spec.system_instructions
        assert "Graffiticode" in spec.system_instructions
        assert spec.few_shot_demos == []
        assert spec.validator_hints.must_compile is True
        assert spec.validator_hints.must_end_with_double_dot is True

    def test_build_spec_with_chunks(self, full_context_pack):
        """Test building spec includes retrieved chunks as demos."""
        spec = build_codegen_prompt_spec(full_context_pack)

        assert len(spec.few_shot_demos) == 2
        assert spec.few_shot_demos[0].prompt == "Create headers"
        assert spec.few_shot_demos[0].code == 'let headers = ["X" "Y"]..'
        assert "L0165" in spec.system_instructions

    def test_build_spec_limits_demos(self):
        """Test that demos are limited to 3."""
        context = ContextPack(
            latest_ask="test",
            constraints=Constraints(dialect="0002"),
            retrieved_chunks=[
                RetrievedChunk(id=f"ex-{i}", prompt=f"prompt {i}", code=f"code {i}..")
                for i in range(5)
            ],
            task_type="codegen",
        )

        spec = build_codegen_prompt_spec(context)
        assert len(spec.few_shot_demos) == 3

    def test_spec_has_required_syntax_rules(self, basic_context_pack):
        """Test that system instructions include key syntax rules."""
        spec = build_codegen_prompt_spec(basic_context_pack)

        system = spec.system_instructions
        assert "let name = value.." in system
        assert "add 1 2" in system or "prefix notation" in system
        assert ".." in system  # Double dot termination


class TestRepairSpec:
    """Tests for repair prompt spec builder."""

    def test_build_repair_spec(self, repair_context_pack):
        """Test building a repair spec."""
        spec = build_repair_prompt_spec(repair_context_pack)

        assert spec.version == "1.0.0"
        assert spec.spec_id.startswith("ps_repair_")
        assert "fixing" in spec.system_instructions.lower() or "fix" in spec.system_instructions.lower()
        assert spec.few_shot_demos == []  # No demos for repair
        assert spec.validator_hints.must_compile is True

    def test_repair_spec_emphasizes_minimal_changes(self, repair_context_pack):
        """Test that repair spec emphasizes minimal changes."""
        spec = build_repair_prompt_spec(repair_context_pack)

        developer = spec.developer_instructions.lower()
        assert "minimal" in developer

    def test_repair_spec_has_error_guidance(self, repair_context_pack):
        """Test that repair spec includes error handling guidance."""
        spec = build_repair_prompt_spec(repair_context_pack)

        system = spec.system_instructions.lower()
        assert "error" in system
        assert ".." in spec.system_instructions  # Double dot guidance
