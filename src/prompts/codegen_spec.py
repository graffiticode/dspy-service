"""Build PromptSpec for code generation tasks."""

import uuid
from typing import TYPE_CHECKING

from src.api.models import (
    FewShotDemo,
    OutputContract,
    PromptSpec,
    ValidatorHints,
)
from src.prompts.templates import (
    DEVELOPER_INSTRUCTIONS_TEMPLATE,
    SYSTEM_INSTRUCTIONS_TEMPLATE,
    USER_TEMPLATE,
)

if TYPE_CHECKING:
    from src.api.models import ContextPack


def build_codegen_prompt_spec(context_pack: "ContextPack") -> PromptSpec:
    """
    Build a PromptSpec for code generation.

    Args:
        context_pack: The context pack containing request, code, examples, etc.

    Returns:
        A PromptSpec ready for rendering into Claude messages.
    """
    dialect = context_pack.constraints.dialect

    # Generate unique spec ID
    spec_id = f"ps_{uuid.uuid4().hex[:12]}"

    # Build system instructions with dialect
    system_instructions = SYSTEM_INSTRUCTIONS_TEMPLATE.format(dialect=dialect)

    # Build developer instructions
    developer_instructions = DEVELOPER_INSTRUCTIONS_TEMPLATE

    # Extract few-shot demos from retrieved chunks
    few_shot_demos = []
    for chunk in context_pack.retrieved_chunks[:3]:  # Limit to 3 demos
        if chunk.prompt and chunk.code:
            few_shot_demos.append(
                FewShotDemo(
                    prompt=chunk.prompt,
                    code=chunk.code,
                )
            )

    # Build user template
    user_template = USER_TEMPLATE

    # Build output contract
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
