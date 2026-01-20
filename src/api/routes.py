"""API routes for DSPy service."""

import logging

from fastapi import APIRouter, HTTPException

from src.api.models import (
    CompilePromptSpecResponse,
    CompileRepairPromptSpecResponse,
    ContextPack,
    PromptSpec,
)
from src.prompts.codegen_spec import build_codegen_prompt_spec
from src.prompts.repair_spec import build_repair_prompt_spec

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/compile-prompt-spec", response_model=CompilePromptSpecResponse)
async def compile_prompt_spec(context_pack: ContextPack) -> CompilePromptSpecResponse:
    """
    Compile a PromptSpec for code generation.

    Takes a ContextPack containing the user's request, current code,
    conversation history, retrieved examples, and constraints.
    Returns a PromptSpec that can be rendered into Claude messages.
    """
    try:
        logger.info(
            f"Compiling prompt spec for dialect {context_pack.constraints.dialect}, "
            f"task_type={context_pack.task_type}"
        )

        # Build the PromptSpec
        prompt_spec = build_codegen_prompt_spec(context_pack)

        logger.info(f"Successfully compiled prompt spec: {prompt_spec.spec_id}")

        return CompilePromptSpecResponse(
            success=True,
            data=prompt_spec,
            error=None,
        )

    except Exception as e:
        logger.error(f"Error compiling prompt spec: {e}", exc_info=True)
        return CompilePromptSpecResponse(
            success=False,
            data=None,
            error=str(e),
        )


@router.post(
    "/compile-repair-prompt-spec", response_model=CompileRepairPromptSpecResponse
)
async def compile_repair_prompt_spec(
    context_pack: ContextPack,
) -> CompileRepairPromptSpecResponse:
    """
    Compile a PromptSpec for error repair.

    Takes a ContextPack with additional repair-specific fields:
    - last_model_output: The code that failed compilation
    - structured_compiler_errors: Parsed error information

    Returns a stricter PromptSpec optimized for fixing errors.
    """
    try:
        # Validate repair-specific fields
        if not context_pack.last_model_output:
            raise ValueError("last_model_output is required for repair tasks")

        if not context_pack.structured_compiler_errors:
            raise ValueError("structured_compiler_errors is required for repair tasks")

        logger.info(
            f"Compiling repair prompt spec for dialect {context_pack.constraints.dialect}, "
            f"error_count={len(context_pack.structured_compiler_errors)}"
        )

        # Build the repair PromptSpec
        prompt_spec = build_repair_prompt_spec(context_pack)

        logger.info(f"Successfully compiled repair prompt spec: {prompt_spec.spec_id}")

        return CompileRepairPromptSpecResponse(
            success=True,
            data=prompt_spec,
            error=None,
        )

    except Exception as e:
        logger.error(f"Error compiling repair prompt spec: {e}", exc_info=True)
        return CompileRepairPromptSpecResponse(
            success=False,
            data=None,
            error=str(e),
        )
