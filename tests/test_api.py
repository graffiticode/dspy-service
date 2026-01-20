"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "dspy-service"
    assert data["status"] == "running"
    assert "version" in data


def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_compile_prompt_spec_basic():
    """Test basic prompt spec compilation."""
    request_body = {
        "latest_ask": "Create a function that doubles a number",
        "current_code": None,
        "conversation_summary": None,
        "retrieved_chunks": [],
        "constraints": {
            "dialect": "0002",
            "max_output_tokens": 4096,
        },
        "task_type": "codegen",
    }

    response = client.post("/compile-prompt-spec", json=request_body)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"] is not None
    assert data["error"] is None

    prompt_spec = data["data"]
    assert prompt_spec["version"] == "1.0.0"
    assert prompt_spec["spec_id"].startswith("ps_")
    assert "system_instructions" in prompt_spec
    assert "user_template" in prompt_spec
    assert "L0002" in prompt_spec["system_instructions"]


def test_compile_prompt_spec_with_chunks():
    """Test prompt spec compilation with retrieved chunks."""
    request_body = {
        "latest_ask": "Create a budget spreadsheet",
        "current_code": 'let title = "Budget"..',
        "conversation_summary": {
            "turn_count": 2,
            "previous_requests": ["Create a spreadsheet"],
            "previous_outputs": None,
        },
        "retrieved_chunks": [
            {
                "id": "example-1",
                "prompt": "Create a table with headers",
                "code": 'let headers = ["A" "B" "C"]..',
                "similarity": 0.85,
            }
        ],
        "constraints": {
            "dialect": "0165",
            "max_output_tokens": 4096,
        },
        "task_type": "codegen",
    }

    response = client.post("/compile-prompt-spec", json=request_body)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True

    prompt_spec = data["data"]
    assert len(prompt_spec["few_shot_demos"]) == 1
    assert prompt_spec["few_shot_demos"][0]["prompt"] == "Create a table with headers"


def test_compile_repair_prompt_spec():
    """Test repair prompt spec compilation."""
    request_body = {
        "latest_ask": "Create a function",
        "current_code": None,
        "conversation_summary": None,
        "retrieved_chunks": [],
        "constraints": {
            "dialect": "0002",
        },
        "task_type": "repair",
        "last_model_output": "let double = <x: mul x 2>",
        "structured_compiler_errors": [
            {
                "type": "syntax",
                "message": "Expected '..' at end of statement",
                "line": 1,
            }
        ],
    }

    response = client.post("/compile-repair-prompt-spec", json=request_body)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True

    prompt_spec = data["data"]
    assert prompt_spec["spec_id"].startswith("ps_repair_")
    assert "minimal changes" in prompt_spec["developer_instructions"].lower()


def test_compile_repair_prompt_spec_missing_output():
    """Test repair fails without last_model_output."""
    request_body = {
        "latest_ask": "Create a function",
        "current_code": None,
        "conversation_summary": None,
        "retrieved_chunks": [],
        "constraints": {
            "dialect": "0002",
        },
        "task_type": "repair",
        "last_model_output": None,
        "structured_compiler_errors": [
            {
                "type": "syntax",
                "message": "Error",
            }
        ],
    }

    response = client.post("/compile-repair-prompt-spec", json=request_body)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is False
    assert "last_model_output" in data["error"]


def test_compile_repair_prompt_spec_missing_errors():
    """Test repair fails without structured_compiler_errors."""
    request_body = {
        "latest_ask": "Create a function",
        "current_code": None,
        "conversation_summary": None,
        "retrieved_chunks": [],
        "constraints": {
            "dialect": "0002",
        },
        "task_type": "repair",
        "last_model_output": "let x = 1",
        "structured_compiler_errors": None,
    }

    response = client.post("/compile-repair-prompt-spec", json=request_body)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is False
    assert "structured_compiler_errors" in data["error"]
