from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from theorem_use_event_instrumentation import TheoremUseEventInstrumenter


def exact_use():
    return {
        "theorem_id": "T003",
        "theorem_authority_id": "PUBLIC_TEST_AUTHORITY",
        "route_step_index": 1,
        "route_provenance": {"provider": "AC124_PUBLIC_TEST"},
        "route_semantics": {
            "schema": "PASS050_ROUTE_ROLE_CONTRACT_V1",
            "status": "EXACT_TYPED_ROUTE_ROLE",
            "required_role": "LOCALIZATION_POLE",
            "provider": "AC124_PUBLIC_TEST",
            "contract_id": "PUBLIC_ROLE_CONTRACT",
        },
    }


def test_verified_edge_emits_complete_event():
    inst = TheoremUseEventInstrumenter(ROOT)
    edge = {"id": "E1", "theorem_use": exact_use()}
    receipt = {"edge_id": "E1", "pass": True}
    out = inst.emit_from_verified_edge(
        root_problem_id="ROOT::PUBLIC_TEST",
        edge=edge,
        edge_receipt=receipt,
    )
    assert out["status"] == "EVENT_EMITTED"
    event = out["event"]
    assert event["required_role"] == "LOCALIZATION_POLE"
    assert event["validation"]["PASS050_bindable"] is True


def test_unverified_edge_emits_no_event():
    inst = TheoremUseEventInstrumenter(ROOT)
    edge = {"id": "E1", "theorem_use": exact_use()}
    receipt = {"edge_id": "E1", "pass": False}
    out = inst.emit_from_verified_edge(
        root_problem_id="ROOT::PUBLIC_TEST",
        edge=edge,
        edge_receipt=receipt,
    )
    assert out["status"] == "NO_EVENT_UNVERIFIED_PROOF_EDGE"
    assert out["event"] is None


def test_direct_role_without_typed_authority_fails_closed():
    inst = TheoremUseEventInstrumenter(ROOT)
    edge = {
        "id": "E1",
        "theorem_use": {
            "theorem_id": "T003",
            "theorem_authority_id": "PUBLIC_TEST_AUTHORITY",
            "route_step_index": 1,
            "route_provenance": {"provider": "AC124_PUBLIC_TEST"},
            "required_role": "LOCALIZATION_POLE",
        },
    }
    receipt = {"edge_id": "E1", "pass": True}
    out = inst.emit_from_verified_edge(
        root_problem_id="ROOT::PUBLIC_TEST",
        edge=edge,
        edge_receipt=receipt,
    )
    assert out["status"] == "EVENT_EMITTED_INCOMPLETE_ROLE"
    assert out["event"]["required_role"] is None
    assert out["event"]["validation"]["PASS050_bindable"] is False


def test_event_identity_is_deterministic_for_same_input():
    inst = TheoremUseEventInstrumenter(ROOT)
    edge = {"id": "E1", "theorem_use": exact_use()}
    receipt = {"edge_id": "E1", "pass": True}
    a = inst.emit_from_verified_edge(
        root_problem_id="ROOT::PUBLIC_TEST",
        edge=edge,
        edge_receipt=receipt,
    )["event"]["event_id"]
    b = inst.emit_from_verified_edge(
        root_problem_id="ROOT::PUBLIC_TEST",
        edge=edge,
        edge_receipt=receipt,
    )["event"]["event_id"]
    assert a == b
