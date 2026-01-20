"""Pydantic models for API request/response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Request Models
# ============================================================================


class RetrievedChunk(BaseModel):
    """A chunk of retrieved context from RAG."""

    id: str = Field(..., description="Unique identifier for the chunk")
    prompt: str = Field(..., description="The prompt/task description")
    code: str = Field(..., description="The code solution")
    similarity: float | None = Field(None, description="Semantic similarity score")
    keyword_score: float | None = Field(None, description="Keyword match score")
    combined_score: float | None = Field(None, description="Combined score")
    tags: list[str] | None = Field(None, description="Tags for categorization")


class ConversationSummary(BaseModel):
    """Summary of conversation history for multi-turn context."""

    turn_count: int = Field(..., description="Number of conversation turns")
    previous_requests: list[str] = Field(
        ..., description="List of previous user requests"
    )
    previous_outputs: list[str] | None = Field(
        None, description="List of previous model outputs"
    )


class Constraints(BaseModel):
    """Constraints for code generation."""

    dialect: str = Field(..., description="The dialect/language ID (e.g., '0002')")
    allowed_builtins: list[str] | None = Field(
        None, description="List of allowed built-in functions"
    )
    max_output_tokens: int | None = Field(
        None, description="Maximum output tokens for generation"
    )


class CompilerError(BaseModel):
    """Structured compiler error information."""

    type: Literal["syntax", "semantic", "unknown"] = Field(
        ..., description="Error classification"
    )
    message: str = Field(..., description="Error message")
    line: int | None = Field(None, description="Line number where error occurred")
    column: int | None = Field(None, description="Column number where error occurred")
    expected: str | None = Field(None, description="What was expected")
    found: str | None = Field(None, description="What was found instead")


class ContextPack(BaseModel):
    """Context pack containing all information for prompt compilation."""

    latest_ask: str = Field(..., description="The user's current request")
    current_code: str | None = Field(None, description="Current code if any")
    conversation_summary: ConversationSummary | None = Field(
        None, description="Summary of conversation history"
    )
    retrieved_chunks: list[RetrievedChunk] = Field(
        default_factory=list, description="Retrieved similar examples"
    )
    constraints: Constraints = Field(..., description="Generation constraints")
    task_type: Literal["codegen", "repair"] = Field(
        "codegen", description="Type of task"
    )

    # Repair-specific fields
    last_model_output: str | None = Field(
        None, description="Last model output (for repair tasks)"
    )
    structured_compiler_errors: list[CompilerError] | None = Field(
        None, description="Structured compiler errors (for repair tasks)"
    )


# ============================================================================
# Response Models
# ============================================================================


class FewShotDemo(BaseModel):
    """A few-shot demonstration example."""

    prompt: str = Field(..., description="The prompt/task")
    code: str = Field(..., description="The code solution")


class OutputContract(BaseModel):
    """Contract specifying expected output format."""

    format: str = Field("code_block", description="Expected format type")
    required_markers: list[str] = Field(
        default_factory=lambda: ["```", ".."],
        description="Required markers in output",
    )


class ValidatorHints(BaseModel):
    """Hints for post-processing and validation."""

    must_compile: bool = Field(True, description="Whether output must compile")
    must_end_with_double_dot: bool = Field(
        True, description="Whether output must end with .."
    )


class PromptSpec(BaseModel):
    """Prompt specification returned by the service."""

    version: str = Field("1.0.0", description="PromptSpec version")
    spec_id: str = Field(..., description="Unique identifier for this spec")
    system_instructions: str = Field(
        ..., description="System-level instructions (hard rules)"
    )
    developer_instructions: str = Field(
        "", description="Developer-level instructions (approach/method)"
    )
    few_shot_demos: list[FewShotDemo] = Field(
        default_factory=list, description="Few-shot demonstration examples"
    )
    user_template: str = Field(
        ..., description="Template for user message with placeholders"
    )
    output_contract: OutputContract = Field(
        default_factory=OutputContract, description="Output format contract"
    )
    validator_hints: ValidatorHints = Field(
        default_factory=ValidatorHints, description="Validation hints"
    )


class CompilePromptSpecResponse(BaseModel):
    """Response wrapper for compile-prompt-spec endpoint."""

    success: bool = Field(..., description="Whether compilation succeeded")
    data: PromptSpec | None = Field(None, description="The compiled PromptSpec")
    error: str | None = Field(None, description="Error message if failed")


class CompileRepairPromptSpecResponse(BaseModel):
    """Response wrapper for compile-repair-prompt-spec endpoint."""

    success: bool = Field(..., description="Whether compilation succeeded")
    data: PromptSpec | None = Field(None, description="The compiled repair PromptSpec")
    error: str | None = Field(None, description="Error message if failed")
