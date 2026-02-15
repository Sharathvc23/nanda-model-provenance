# Model Identity Metadata for Federated AI Agent Discovery

**Authors:** StellarMinds ([stellarminds.ai](https://stellarminds.ai))
**Date:** February 2026
**Version:** 1.0

## Abstract

Federated AI agent registries require a lightweight, standardized way to advertise model identity — the "who" of a model — separate from richer concerns like integrity verification, lifecycle management, and cryptographic governance. Existing provenance formats tend to either bundle identity with verification metadata (requiring cryptographic dependencies) or embed it in documentation-oriented schemas not designed for machine-readable network protocols. This paper presents `nanda-model-provenance`, a zero-dependency Python dataclass that captures model identity and versioning in eight typed fields and serializes them into three distinct JSON shapes expected by the NANDA agent ecosystem: AgentFacts metadata extensions, AgentCard model information, and decision-envelope provenance records. The implementation uses an omit-when-empty serialization pattern that produces compact payloads suitable for network transmission, a vendor-neutral extension key (`x_model_provenance`) following the NANDA `x_` prefix convention with opt-in vendor namespacing, and forward-compatible deserialization that silently ignores unknown keys. The library serves as the foundational identity layer upon which the `nanda-model-card`, `nanda-model-integrity-layer`, and `nanda-model-governance` packages build progressively richer metadata, verification, and approval semantics. The implementation uses only the Python standard library, ships with 26 tests including golden-file contract tests pinned to production JSON shapes, and passes strict static analysis.

## 1. Introduction

### 1.1 Problem Statement

When an AI agent in a decentralized registry advertises its capabilities, consuming agents and orchestrators need to answer a foundational question: *"What model is this agent using, and where did it come from?"* This model identity information — the model's name, version, inference provider, type, and governance classification — is the prerequisite for all downstream trust decisions.

In practice, this identity metadata is often entangled with heavier concerns. Integrity verification systems bundle identity with cryptographic hashing and attestation. Model card schemas embed identity within rich documentation formats with lifecycle management and training metrics. Governance frameworks wrap identity in approval workflows and signature chains. Each coupling introduces dependencies and complexity that may not be appropriate for every consumer.

A registry that simply wants to advertise "this agent uses llama-3.1-8b via ollama" should not need to import a cryptography library, parse a lifecycle state machine, or understand quorum signatures. The identity layer needs to stand alone.

### 1.2 Motivation

The NANDA (Network of AI Agents in Decentralized Architecture) ecosystem defines three distinct integration points where model identity metadata appears:

1. **AgentFacts** — The primary agent metadata record in NANDA registries, where model provenance appears as a vendor extension under an `x_`-prefixed key.
2. **AgentCard** — A human- and machine-readable agent profile, where model information appears under a `model_info` key.
3. **Decision envelopes** — Audit records for agent decisions, where only the minimal identity fields (`model_id`, `model_version`, `provider_id`) appear as flat top-level fields.

Each integration point expects a different JSON shape from the same underlying data. A provenance library must serialize identity metadata into all three shapes without requiring consumers to understand the structural differences.

### 1.3 Contributions

This paper makes the following contributions:

- A **single dataclass with eight fields** that captures model identity metadata — model identifier, version, inference provider, model type, base model, governance tier, weights hash, and risk level — with only `model_id` required.
- **Three serialization methods** that produce the exact JSON shapes expected by NANDA AgentFacts extensions, AgentCard metadata, and decision-envelope records.
- An **omit-when-empty serialization pattern** using truthiness filtering (`{k: v for ... if v}`) that produces compact payloads by excluding empty-string fields.
- **Forward-compatible deserialization** that silently ignores unknown keys, allowing the library to consume provenance records from future schema versions without breaking.
- A **vendor-neutral extension key** (`x_model_provenance`) with an opt-in `extension_key` parameter for vendor-specific namespacing.
- **Golden-file contract tests** that pin the library's JSON output against the exact shapes produced by the original monolithic implementation, ensuring safe extraction without breaking consumers.
- A **zero-dependency implementation** using only Python's `dataclasses` module, suitable for constrained environments from edge devices to serverless functions.

## 2. Related Work

### 2.1 ML Metadata (MLMD)

Google's ML Metadata library, part of the TFX ecosystem, provides a relational schema for tracking artifacts, executions, and contexts across ML pipelines. MLMD excels at pipeline lineage — linking training runs to datasets to model artifacts — but it is designed around a gRPC metadata store and a relational query model. For federated agent discovery, where metadata must be serialized into JSON payloads for network transmission, MLMD's store-coupled architecture introduces dependencies that may not be appropriate. MLMD also does not currently provide the multi-target serialization (AgentFacts, AgentCard, decision envelope) that NANDA integration requires.

### 2.2 W3C PROV Data Model (PROV-DM)

The W3C PROV Data Model provides a general-purpose provenance standard based on entities, activities, and agents. PROV-DM can express rich derivation chains (e.g., "this model was derived from that dataset by this training activity"). However, its generality means it does not provide ML-specific fields (`model_type`, `governance_tier`, `base_model`) and its graph-based representation requires RDF or PROV-JSON serialization, which is more complex than the flat key-value structures expected by NANDA agent metadata extensions.

### 2.3 SLSA Provenance

The SLSA (Supply-chain Levels for Software Artifacts) v1.0 provenance predicate captures build provenance — builder identity, source references, and build configuration — for software artifacts. While SLSA's approach to provenance attestation informs supply-chain security broadly, it is designed for software build artifacts (container images, binaries) rather than ML model identity. SLSA provenance does not currently capture ML-specific concepts like model type taxonomies, inference provider identifiers, or governance tier classifications.

### 2.4 Model Cards (Mitchell et al., 2019)

Model Cards, introduced by Mitchell et al., provide structured documentation for trained ML models covering intended use, evaluation metrics, and ethical considerations. Model Cards are primarily documentation artifacts designed for human consumption and transparency reporting. They are not currently designed as lightweight serializable identity types for machine-readable network protocols. The companion `nanda-model-card` package addresses the richer "what is this model?" question with lifecycle management, validation, and training metrics; `nanda-model-provenance` intentionally addresses only the narrower "where did this model come from?" identity question.

### 2.5 Gaps Addressed

This work addresses three gaps in the existing landscape:

1. **ML-specific identity without verification coupling** — a provenance type that captures model identity fields (type, provider, governance tier) without requiring cryptographic dependencies for hashing, signing, or attestation.
2. **Multi-target serialization** — a single source of truth that serializes into three distinct JSON shapes for three different NANDA integration points.
3. **Minimal, composable foundation** — a zero-dependency identity layer that richer packages (integrity verification, governance) can build upon without inheriting unnecessary complexity.

## 3. Design / Architecture

### 3.1 Core Data Model

The `ModelProvenance` dataclass captures eight fields organized into three semantic groups:

**Identity fields:** `model_id` (the only required field), `model_version` (semantic or arbitrary version string), `provider_id` (inference provider — e.g., `"openai"`, `"ollama"`, `"local"`).

**Classification fields:** `model_type` (paradigm category — `"base"`, `"lora_adapter"`, `"onnx_edge"`, `"federated"`, `"heuristic"`), `base_model` (foundation model name for adapter types), `governance_tier` (`"standard"` or `"regulated"`).

**Integrity-linking fields:** `weights_hash` (SHA-256 hex digest of model weights), `risk_level` (`"low"`, `"medium"`, `"high"`). These fields allow provenance records to carry integrity-relevant metadata without depending on the integrity layer itself.

### 3.2 Three Serialization Targets

The library produces three distinct JSON shapes from the same underlying data:

```
ModelProvenance
    ├── to_agentfacts_extension()  →  {"x_model_provenance": {...}}
    ├── to_agent_card_metadata()   →  {"model_info": {...}}
    └── to_decision_fields()       →  {"model_id": ..., "provider_id": ...}
```

| Method | JSON Shape | Fields | Use Case |
|--------|-----------|--------|----------|
| `to_agentfacts_extension()` | Nested under extension key | All non-empty | NANDA AgentFacts `metadata` |
| `to_agent_card_metadata()` | Nested under `model_info` | All non-empty | NANDA AgentCard profile |
| `to_decision_fields()` | Flat top-level | `model_id`, `model_version`, `provider_id` only | Decision audit records |

The first two methods include all non-empty fields, producing a complete provenance snapshot. The third deliberately restricts output to three identity-core fields, matching the minimal provenance footprint expected in decision-envelope audit records where payload size matters.

### 3.3 Omit-When-Empty Pattern

All serialization methods implement an omit-when-empty pattern: fields with empty-string values are excluded from output. This design produces compact JSON payloads by default — a `ModelProvenance` with only `model_id` set serializes to `{"model_id": "llama-3.1-8b"}` rather than carrying seven empty-string fields.

The pattern is implemented via truthiness filtering:

```python
{k: v for k, v in {field_map}.items() if v}
```

This mirrors the exact filter pattern used in NANDA bridge implementations, ensuring byte-identical output between the extracted library and the original monolithic code.

### 3.4 Key Design Decisions

**Empty strings over `Optional[str]`.** All optional fields default to `""` rather than `None`. This enables the truthiness filter pattern (`if v`) to work uniformly — both `""` and `None` are falsy, but empty strings avoid the need for `Optional` type annotations, simplify equality comparisons, and produce cleaner `repr()` output. The trade-off is that the type signature `str` does not distinguish "not set" from "explicitly set to empty," but in practice provenance fields are never meaningfully set to empty strings.

**Dataclass over Pydantic.** Using Python's `@dataclass` rather than Pydantic models eliminates all runtime dependencies. The provenance type is intentionally a plain data container without validation logic — field validation is the responsibility of the integrity layer and governance layer, which operate at higher abstraction levels.

**No enum validation.** Fields like `model_type`, `governance_tier`, and `risk_level` accept arbitrary strings rather than validating against an enum. This keeps the provenance layer forward-compatible with new values added by downstream packages and avoids coupling the identity layer to classification decisions that belong at the policy level.

**Vendor-neutral default key.** The AgentFacts extension key defaults to `x_model_provenance` rather than a vendor-specific namespace (e.g., `x_lyra_space`). The `extension_key` parameter enables vendor-specific namespacing when needed, but the default promotes interoperability across registries.

## 4. Implementation

### 4.1 The ModelProvenance Dataclass

The core implementation resides in a single module (`provenance.py`). The class uses Python's `@dataclass` decorator with carefully chosen defaults:

```python
@dataclass
class ModelProvenance:
    model_id: str
    model_version: str = ""
    provider_id: str = ""
    model_type: str = ""
    base_model: str = ""
    governance_tier: str = ""
    weights_hash: str = ""
    risk_level: str = ""
```

The `from __future__ import annotations` import enables PEP 604 union syntax and deferred annotation evaluation, supporting Python 3.10+ while maintaining forward-compatible type hints.

### 4.2 Full-Field Serialization: `to_dict()`

The `to_dict()` method constructs an explicit field map rather than using `dataclasses.asdict()`:

```python
def to_dict(self) -> dict[str, str]:
    return {
        k: v
        for k, v in {
            "model_id": self.model_id,
            "model_version": self.model_version,
            # ... all 8 fields
        }.items()
        if v
    }
```

The explicit map is a deliberate choice over `dataclasses.asdict()` for two reasons: it controls field ordering (matching the NANDA bridge's expected order), and it avoids the deep-copy behavior of `asdict()` which would be unnecessary overhead for a flat string-only dataclass.

### 4.3 AgentFacts Extension: `to_agentfacts_extension()`

```python
def to_agentfacts_extension(
    self,
    extension_key: str = "x_model_provenance",
) -> dict[str, dict[str, str]]:
    return {extension_key: self.to_dict()}
```

The method wraps `to_dict()` output under a single key, producing the nested structure expected by NANDA AgentFacts `metadata` extensions. The `x_` prefix follows the NANDA convention for vendor extensions, analogous to HTTP's `X-` header prefix convention.

### 4.4 AgentCard Metadata: `to_agent_card_metadata()`

```python
def to_agent_card_metadata(self) -> dict[str, dict[str, str]]:
    return {"model_info": self.to_dict()}
```

The fixed `model_info` key matches the NANDA AgentCard specification. Unlike the AgentFacts method, the key is not parameterized because the AgentCard schema defines `model_info` as a reserved key.

### 4.5 Decision Envelope Fields: `to_decision_fields()`

```python
def to_decision_fields(self) -> dict[str, str]:
    result: dict[str, str] = {}
    if self.model_id:
        result["model_id"] = self.model_id
    if self.model_version:
        result["model_version"] = self.model_version
    if self.provider_id:
        result["provider_id"] = self.provider_id
    return result
```

This method deliberately restricts output to three fields rather than delegating to `to_dict()`. Decision envelopes are audit records where payload minimality matters — including `model_type`, `governance_tier`, or `weights_hash` in every decision record would add noise to audit logs. The explicit field-by-field construction (rather than filtering `to_dict()`) makes the restriction visible and intentional.

### 4.6 Forward-Compatible Deserialization: `from_dict()`

```python
@classmethod
def from_dict(cls, data: dict[str, str]) -> ModelProvenance:
    if "model_id" not in data:
        msg = "model_id is required"
        raise TypeError(msg)
    return cls(
        model_id=data["model_id"],
        model_version=data.get("model_version", ""),
        # ... remaining fields via .get() with "" default
    )
```

Two design choices enable forward compatibility:

1. **Unknown keys are silently ignored** — `from_dict()` reads only the eight known fields via `.get()`. If a future schema version adds a ninth field, existing library versions can still deserialize the record without error.
2. **`TypeError` for missing `model_id`** — The single required field raises `TypeError` (not `ValueError`) to align with Python's convention for missing required arguments.

### 4.7 Public API

The package exports two symbols from its `__init__.py`:

| Export | Type | Purpose |
|--------|------|---------|
| `ModelProvenance` | class | Core identity metadata schema |
| `__version__` | str | Package version (`"0.1.0"`) |

## 5. Integration

### 5.1 NANDA Ecosystem Context

The `nanda-model-provenance` package occupies the **identity layer** in the NANDA ecosystem, answering the question: *"Where did this model come from?"* It provides the foundational metadata type that three companion packages build upon:

| Package | Role | Question Answered |
|---------|------|-------------------|
| `nanda-model-provenance` | Identity metadata | Where did this model come from? |
| `nanda-model-card` | Metadata schema | What is this model? |
| `nanda-model-integrity-layer` | Integrity verification | Does this model's metadata meet policy? |
| `nanda-model-governance` | Cryptographic governance | Has this model been approved? |

### 5.2 Integration with the Model Card Schema

The `nanda-model-card` package defines a richer `ModelCard` dataclass with 20 fields covering lifecycle status, training metrics, and dataset provenance. Several model card fields map directly to provenance fields:

- **`ModelCard.model_id`** → **`ModelProvenance.model_id`**
- **`ModelCard.model_type`** → **`ModelProvenance.model_type`**
- **`ModelCard.base_model`** → **`ModelProvenance.base_model`**
- **`ModelCard.weights_hash`** → **`ModelProvenance.weights_hash`**
- **`ModelCard.risk_level`** → **`ModelProvenance.risk_level`**

This field alignment is by design: provenance carries the identity subset of model card metadata, allowing systems that only need "who is this model" to avoid the full model card dependency.

### 5.3 Integration with the Integrity Layer

The `nanda-model-integrity-layer` defines its own `ModelProvenance` dataclass with 11 fields — the same 8 fields as this package plus `hash_algorithm`, `created_at`, and `attestation_method`. The integrity layer's provenance type extends the identity concern with verification-specific metadata. The three additional fields capture *how* and *when* provenance was verified, which belongs at the integrity layer rather than the identity layer.

The integrity layer's `ModelLineage.from_provenance()` method consumes `model_id`, `base_model`, and `model_type` to reconstruct derivation chains. Its governance policy engine (`check_governance()`) reads `weights_hash`, `governance_tier`, and `risk_level` to enforce compliance rules. All of these fields originate from the identity schema defined here.

### 5.4 Integration with the Governance Layer

The `nanda-model-governance` package uses provenance fields at two points in its three-plane workflow:

- **Training completion** — `GovernanceCoordinator.complete_training()` captures `model_id` and `weights_hash` in the `TrainingOutput` handoff, establishing the identity anchor for the governance decision.
- **Integrity bridge** — The governance layer's `create_provenance_with_approval()` function creates provenance records populated with governance metadata, linking the cryptographic approval back to model identity.

### 5.5 Agent Discovery Workflow

In a NANDA agent discovery flow, provenance metadata participates at each stage:

1. **Registration** — An agent's `ModelProvenance` is serialized via `to_agentfacts_extension()` and merged into the agent's AgentFacts metadata.
2. **Discovery** — A consuming agent queries the registry, receives AgentFacts, and extracts the inner provenance dict from the `x_model_provenance` key.
3. **Reconstruction** — The consumer calls `ModelProvenance.from_dict()` on the extracted dict to reconstruct a typed provenance object.
4. **Routing** — The consumer uses `model_type`, `provider_id`, and `governance_tier` to make routing decisions without needing the full integrity or governance stack.

## 6. Evaluation

### 6.1 Test Coverage

The test suite contains **26 test methods** across 2 test modules:

| Test Module | Tests | Coverage Area |
|-------------|:-----:|---------------|
| `test_provenance.py` | 17 | Serialization, AgentFacts, AgentCard, decision fields, round-trip, deserialization |
| `test_json_shapes.py` | 9 | Golden-file contract tests against production JSON shapes |

All tests pass under `pytest` with strict mode. The codebase passes `mypy --strict` static analysis.

### 6.2 Golden-File Contract Tests

The `test_json_shapes.py` module implements **contract tests** that pin the library's JSON output against the exact shapes produced by four specific locations in the original monolithic codebase:

| Test Class | Pinned Against | Validates |
|------------|---------------|-----------|
| `TestAgentFactsShape` | `nanda_bridge.py` line 718 | AgentFacts extension inner dict matches `_to_nanda_agentfacts` output |
| `TestAgentCardShape` | `nanda_bridge.py` line 1065 | AgentCard `model_info` matches `_profile_to_agent_card` output |
| `TestDecisionEnvelopeShape` | `envelope.py` lines 157–163 | Decision fields match `DecisionEnvelope.to_dict()` provenance block |
| `TestSetModelInfoFilterPattern` | `agents/base.py` lines 181–192 | `to_dict()` filter pattern matches `BaseAgent.set_model_info()` output |

These tests serve as the extraction safety net: if the library's serialization diverges from what the monolith produced, the golden-file tests fail, preventing silent contract breakage.

### 6.3 Example: Registration and Discovery Round-Trip

```python
from nanda_model_provenance import ModelProvenance

# Agent registration side
provenance = ModelProvenance(
    model_id="phi3-mini",
    model_version="3.8b",
    provider_id="local",
    model_type="lora_adapter",
    base_model="llama-3.1-8b",
    governance_tier="standard",
)

# Serialize for AgentFacts
agent_metadata = {"name": "My Agent", "version": "1.0"}
agent_metadata.update(provenance.to_agentfacts_extension())
# agent_metadata now includes x_model_provenance key

# Discovery side — extract and reconstruct
inner = agent_metadata["x_model_provenance"]
rebuilt = ModelProvenance.from_dict(inner)
assert rebuilt == provenance  # Lossless round-trip
```

### 6.4 Serialization Compactness

The omit-when-empty pattern produces minimal payloads:

```python
# Minimal provenance — 1 field set
ModelProvenance(model_id="test").to_dict()
# → {"model_id": "test"}

# Typical provenance — 3 fields set
ModelProvenance(model_id="phi3", provider_id="local", governance_tier="standard").to_dict()
# → {"model_id": "phi3", "provider_id": "local", "governance_tier": "standard"}

# Full provenance — all 8 fields set
# → all 8 key-value pairs, no empty strings
```

## 7. Conclusion

### 7.1 Summary

This paper presented `nanda-model-provenance`, a minimal identity metadata type for federated AI agent discovery. By restricting scope to model identity — eight fields, three serialization targets, zero dependencies — the library provides a composable foundation that avoids coupling identity with verification, lifecycle, or governance concerns. The omit-when-empty pattern and multi-target serialization address the practical requirement of embedding model identity in diverse NANDA protocol structures. The golden-file contract tests ensure extraction fidelity from the original monolithic implementation.

### 7.2 Future Work

Several directions merit further investigation:

- **Schema registry integration** — Publishing the `ModelProvenance` field schema as a JSON Schema document, enabling registry-side validation without importing the Python package.
- **Content-addressable provenance** — Computing a deterministic hash of the provenance record itself (not just the weights), enabling provenance records to be referenced by content address in distributed registries.
- **Provenance chaining** — Adding an optional `parent_provenance_hash` field to link provenance records across model derivation steps, complementing the integrity layer's lineage chains with a lighter-weight identity-only mechanism.
- **Multi-model provenance** — Supporting agents that use multiple models (e.g., an ensemble or a routing layer) through a collection-valued provenance extension.

## References

1. Google. "ML Metadata (MLMD)." TensorFlow Extended Documentation. https://www.tensorflow.org/tfx/guide/mlmd

2. Moreau, L. and Missier, P. (2013). "PROV-DM: The PROV Data Model." W3C Recommendation. https://www.w3.org/TR/prov-dm/

3. SLSA. "Supply-chain Levels for Software Artifacts: Provenance." https://slsa.dev/provenance

4. Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I.D., and Gebru, T. (2019). "Model Cards for Model Reporting." *Proceedings of the Conference on Fairness, Accountability, and Transparency (FAT\*)*, pp. 220–229.

5. NANDA Protocol. "Network of AI Agents in Decentralized Architecture." https://projectnanda.org

6. Python Software Foundation. "dataclasses — Data Classes." Python 3.10+ Documentation. https://docs.python.org/3/library/dataclasses.html
