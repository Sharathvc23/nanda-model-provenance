"""Golden-file tests verifying JSON shapes match NANDA bridge patterns.

These tests encode the exact JSON structures produced by Lyra's
nanda_bridge.py so the library stays aligned with real-world usage.
"""

from __future__ import annotations

from nanda_model_provenance import ModelProvenance


# -- AgentFacts extension shape (mirrors nanda_bridge line 718) -------


class TestAgentFactsShape:
    """AgentFacts extension matches x_lyra_space.model_info pattern."""

    def test_matches_lyra_agentfacts_model_info(self):
        """The inner dict matches what Lyra puts in x_lyra_space.model_info."""
        p = ModelProvenance(
            model_id="phi3-mini",
            provider_id="local",
            governance_tier="STANDARD",
        )
        ext = p.to_agentfacts_extension()
        inner = ext["x_model_provenance"]

        # Exact match with the dict Lyra's _to_nanda_agentfacts produces
        assert inner == {
            "model_id": "phi3-mini",
            "provider_id": "local",
            "governance_tier": "STANDARD",
        }

    def test_lyra_extension_key_differs(self):
        """Library uses x_model_provenance, not x_lyra_space (vendor-neutral)."""
        p = ModelProvenance(model_id="test")
        ext = p.to_agentfacts_extension()
        assert "x_model_provenance" in ext
        assert "x_lyra_space" not in ext

    def test_custom_vendor_key(self):
        """Vendors can use their own namespace via extension_key arg."""
        p = ModelProvenance(model_id="test")
        ext = p.to_agentfacts_extension(extension_key="x_lyra_space")
        assert "x_lyra_space" in ext


# -- AgentCard metadata shape (mirrors nanda_bridge line 1065) --------


class TestAgentCardShape:
    """AgentCard metadata matches the model_info pattern."""

    def test_matches_lyra_agent_card_metadata(self):
        """model_info key with inner dict matches Lyra's _profile_to_agent_card."""
        p = ModelProvenance(
            model_id="llama-3.1-8b",
            provider_id="ollama",
        )
        card_meta = p.to_agent_card_metadata()
        assert card_meta == {
            "model_info": {
                "model_id": "llama-3.1-8b",
                "provider_id": "ollama",
            }
        }

    def test_absent_model_info_is_minimal(self):
        """Minimal provenance produces minimal model_info."""
        p = ModelProvenance(model_id="test-model")
        card_meta = p.to_agent_card_metadata()
        assert card_meta == {"model_info": {"model_id": "test-model"}}


# -- Decision envelope shape (mirrors envelope.py lines 157-163) -----


class TestDecisionEnvelopeShape:
    """Decision fields match DecisionEnvelope.to_dict() provenance block."""

    def test_matches_envelope_to_dict_pattern(self):
        """Top-level model_id/model_version/provider_id — omit-when-falsy."""
        p = ModelProvenance(
            model_id="phi3-mini",
            model_version="3.8b",
            provider_id="local",
        )
        fields = p.to_decision_fields()
        assert fields == {
            "model_id": "phi3-mini",
            "model_version": "3.8b",
            "provider_id": "local",
        }

    def test_partial_matches_envelope_pattern(self):
        """When model_version is absent, omitted like envelope.to_dict()."""
        p = ModelProvenance(model_id="phi3-mini", provider_id="local")
        fields = p.to_decision_fields()
        assert fields == {"model_id": "phi3-mini", "provider_id": "local"}
        assert "model_version" not in fields


# -- set_model_info filter pattern (mirrors agents/base.py:181-192) ---


class TestSetModelInfoFilterPattern:
    """to_dict() mirrors BaseAgent.set_model_info() {if v} filter."""

    def test_matches_set_model_info_output(self):
        """Exact field set produced by set_model_info with all args."""
        p = ModelProvenance(
            model_id="phi3-mini",
            model_version="3.8b",
            provider_id="local",
            model_type="lora_adapter",
            base_model="llama-3.1-8b",
            governance_tier="STANDARD",
        )
        d = p.to_dict()
        # These 6 fields are exactly what set_model_info produces
        assert set(d.keys()) == {
            "model_id",
            "model_version",
            "provider_id",
            "model_type",
            "base_model",
            "governance_tier",
        }

    def test_extra_fields_from_model_card(self):
        """weights_hash and risk_level extend beyond set_model_info."""
        p = ModelProvenance(
            model_id="test",
            weights_hash="abc123",
            risk_level="high",
        )
        d = p.to_dict()
        assert "weights_hash" in d
        assert "risk_level" in d
        # But to_dict() output is still a valid superset
        assert d["model_id"] == "test"
