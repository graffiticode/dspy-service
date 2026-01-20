# DSPy Service

A Python-based service for compiling prompt specifications for the Graffiticode code generation pipeline.

## Overview

The DSPy service provides structured `PromptSpec` objects that define how to construct Claude prompts, while the Node.js console retains ownership of orchestration, RAG, Claude API calls, and validation.

## Architecture

```
User → Node → RAG → DSPy(PromptSpec) → renderPrompt → Claude → validate
                          ↑                                       ↓
                    DSPy(RepairSpec) ←──── semantic errors ←──────┘
```

## API Endpoints

### POST `/compile-prompt-spec`

Compile a PromptSpec for code generation.

**Request:**
```json
{
  "latest_ask": "Create a budget spreadsheet",
  "current_code": "let title = \"Budget\"..",
  "conversation_summary": {
    "turn_count": 2,
    "previous_requests": ["Create empty spreadsheet"]
  },
  "retrieved_chunks": [
    {
      "id": "ex-1",
      "prompt": "Create table headers",
      "code": "let headers = [\"A\" \"B\"]..",
      "similarity": 0.85
    }
  ],
  "constraints": {
    "dialect": "0165",
    "max_output_tokens": 4096
  },
  "task_type": "codegen"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "spec_id": "ps_abc123",
    "system_instructions": "You are a Graffiticode assistant...",
    "developer_instructions": "APPROACH: 1. Analyze request...",
    "few_shot_demos": [...],
    "user_template": "<USER_REQUEST>...",
    "output_contract": { "format": "code_block", "required_markers": ["```", ".."] },
    "validator_hints": { "must_compile": true, "must_end_with_double_dot": true }
  }
}
```

### POST `/compile-repair-prompt-spec`

Compile a PromptSpec for error repair (stricter, minimal-diff rules).

**Additional request fields:**
```json
{
  "task_type": "repair",
  "last_model_output": "let broken = ...",
  "structured_compiler_errors": [
    { "type": "syntax", "message": "Expected '..'", "line": 5 }
  ]
}
```

### GET `/health`

Health check endpoint.

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### Running Locally

```bash
# Run the service
python -m src.main

# Or with uvicorn directly
uvicorn src.main:app --reload --port 8080
```

### Running Tests

```bash
pytest tests/ -v
```

### Docker

```bash
# Build
docker build -t dspy-service .

# Run
docker run -p 8080:8080 dspy-service
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8080` | Server port |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `info` | Logging level |

## Project Structure

```
dspy-service/
├── src/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration management
│   ├── api/
│   │   ├── routes.py        # API endpoints
│   │   └── models.py        # Pydantic models
│   ├── prompts/
│   │   ├── codegen_spec.py  # Code generation PromptSpec builder
│   │   ├── repair_spec.py   # Repair PromptSpec builder
│   │   └── templates.py     # Instruction templates
│   └── selectors/
│       └── few_shot_selector.py  # Few-shot selection (Phase 4)
├── tests/
│   ├── test_api.py          # API endpoint tests
│   └── test_prompts.py      # Prompt builder tests
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Integration with Console

In the console `.env`, add:

```
ENABLE_DSPY_SERVICE=true
DSPY_SERVICE_URL=http://localhost:8080
DSPY_TIMEOUT_MS=5000
DSPY_FALLBACK_TO_LEGACY=true
```

## Roadmap

- **Phase 1** (Current): Template-based PromptSpec generation
- **Phase 2**: Node.js integration (complete)
- **Phase 3**: Error classification and repair flow
- **Phase 4**: DSPy library integration for learned few-shot selection
