"""Build PromptSpec for error repair tasks."""

import uuid
from typing import TYPE_CHECKING

from src.api.models import (
    FewShotDemo,
    OutputContract,
    PromptSpec,
    ValidatorHints,
)
from src.prompts.templates import (
    REPAIR_DEVELOPER_INSTRUCTIONS_TEMPLATE,
    REPAIR_SYSTEM_INSTRUCTIONS_TEMPLATE,
    REPAIR_USER_TEMPLATE,
)

if TYPE_CHECKING:
    from src.api.models import ContextPack


def build_repair_prompt_spec(context_pack: "ContextPack") -> PromptSpec:
    """
    Build a PromptSpec for error repair.

    This generates a stricter PromptSpec optimized for fixing compilation errors.
    It emphasizes minimal changes and focuses on the specific errors.

    Args:
        context_pack: The context pack with repair-specific fields:
            - last_model_output: The code that failed
            - structured_compiler_errors: Parsed error information

    Returns:
        A PromptSpec optimized for error repair.
    """
    dialect = context_pack.constraints.dialect

    # Generate unique spec ID
    spec_id = f"ps_repair_{uuid.uuid4().hex[:12]}"

    # Build system instructions (repair-specific)
    system_instructions = REPAIR_SYSTEM_INSTRUCTIONS_TEMPLATE

    # Build developer instructions (repair-specific)
    developer_instructions = REPAIR_DEVELOPER_INSTRUCTIONS_TEMPLATE

    # For repair tasks, we typically don't include few-shot demos
    # to keep the context focused on the specific error
    few_shot_demos: list[FewShotDemo] = []

    # Build user template (repair-specific)
    user_template = REPAIR_USER_TEMPLATE

    # Build output contract (stricter for repairs)
    output_contract = OutputContract(
        format="code_block",
        required_markers=["```", ".."],
    )

    # Build validator hints
    validator_hints = ValidatorHints(
        must_compile=True,
        must_end_with_double_dot=True,
    )

    return PromptSpec(
        version="1.0.0",
        spec_id=spec_id,
        system_instructions=system_instructions,
        developer_instructions=developer_instructions,
        few_shot_demos=few_shot_demos,
        user_template=user_template,
        output_contract=output_contract,
        validator_hints=validator_hints,
    )
