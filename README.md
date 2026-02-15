# nanda-model-provenance

Model provenance metadata for [NANDA](https://github.com/google/A2A)-compatible agent discovery.

A single `ModelProvenance` dataclass that serializes model-related metadata into the JSON shapes expected by NANDA AgentFacts, AgentCard, and decision-envelope outputs. Zero runtime dependencies.

## Install

```bash
pip install nanda-model-provenance
```

## Quick Start

```python
from nanda_model_provenance import ModelProvenance

provenance = ModelProvenance(
    model_id="llama-3.1-8b",
    model_version="1.0.0",
    provider_id="ollama",
    model_type="base",
    governance_tier="standard",
)

# For NANDA AgentFacts metadata extension
provenance.to_agentfacts_extension()
# {"x_model_provenance": {"model_id": "llama-3.1-8b", "model_version": "1.0.0", ...}}

# For NANDA AgentCard metadata
provenance.to_agent_card_metadata()
# {"model_info": {"model_id": "llama-3.1-8b", ...}}

# For decision envelope records
provenance.to_decision_fields()
# {"model_id": "llama-3.1-8b", "model_version": "1.0.0", "provider_id": "ollama"}
```

## Field Reference

| Field | Required | Description |
|---|---|---|
| `model_id` | Yes | Model identifier (e.g. `"llama-3.1-8b"`) |
| `model_version` | No | Semantic or arbitrary version string |
| `provider_id` | No | Inference provider (`"openai"`, `"ollama"`, `"local"`) |
| `model_type` | No | `"base"`, `"lora_adapter"`, `"onnx_edge"`, `"federated"`, `"heuristic"` |
| `base_model` | No | Foundation model name (when model_type is an adapter) |
| `governance_tier` | No | `"standard"` or `"regulated"` |
| `weights_hash` | No | SHA-256 hex digest of model weights |
| `risk_level` | No | `"low"`, `"medium"`, or `"high"` |

All optional fields default to `""` and are omitted from serialized output.

## Output Methods

| Method | JSON Shape | Use Case |
|---|---|---|
| `to_dict()` | `{"model_id": ..., ...}` | Raw provenance dict |
| `to_agentfacts_extension()` | `{"x_model_provenance": {...}}` | NANDA AgentFacts metadata |
| `to_agent_card_metadata()` | `{"model_info": {...}}` | NANDA AgentCard metadata |
| `to_decision_fields()` | `{"model_id": ..., "provider_id": ...}` | Decision envelope records |
| `from_dict(data)` | — | Deserialize from dict |

## Extension Key

The default AgentFacts extension key is `x_model_provenance` (vendor-neutral, following the NANDA `x_` prefix convention). To use a vendor-specific namespace:

```python
provenance.to_agentfacts_extension(extension_key="x_myvendor")
```

## Related Packages

| Package | Question it answers |
|---------|-------------------|
| `nanda-model-provenance` (this package) | "Where did this model come from?" (identity, versioning, provider, NANDA serialization) |
| [`model-card`](https://github.com/Sharathvc23/model-card) | "What is this model?" (unified metadata schema — type, status, risk level, metrics, weights hash) |
| [`nanda-model-integrity-layer`](https://github.com/Sharathvc23/nanda-model-integrity-layer) | "Does this model's metadata meet policy?" (rule-based checks) |
| [`nanda-model-governance`](https://github.com/Sharathvc23/nanda-governance) | "Has this model been cryptographically approved for deployment?" (approval flow with signatures, quorum, scoping, revocation) |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

Apache-2.0
