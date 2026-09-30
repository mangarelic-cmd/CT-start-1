from __future__ import annotations
from pathlib import Path
import hashlib, json
from typing import Any, Dict, Iterable, List, Optional


def _canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _digest(x: Any) -> str:
    return hashlib.sha256(_canon(x).encode()).hexdigest()


class TheoremUseEventInstrumenter:
    """Emit problem-local theorem-use events only from verified proof applications.

    This layer deliberately separates four objects:
      * theorem-fabric search/candidate routes;
      * theorem-schema proof occurrences;
      * verified problem-application theorem uses;
      * PASS050 contextual address bindings.

    A search candidate never emits an event. A proof edge emits only after its proof rule
    has been independently verified by the reconstruction kernel.
    """

    EVENT_SCHEMA = "PROBLEM_APPLICATION_THEOREM_USE_EVENT_V1"
    ROLE_SCHEMA = "PASS050_ROUTE_ROLE_CONTRACT_V1"
    REQUIRED = (
        "root_problem_id",
        "route_occurrence_id",
        "theorem_id",
        "theorem_authority_id",
        "route_step_index",
        "route_provenance",
        "required_role",
    )

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root).resolve() if root else Path(__file__).resolve().parents[1]

    def adapt_role(self, theorem_use: Dict[str, Any]) -> Dict[str, Any]:
        """Return a PASS050 role only from an explicit typed route-semantics contract."""
        direct = theorem_use.get("required_role")
        if direct:
            auth = theorem_use.get("role_authority") or {}
            if auth.get("status") == "EXACT_TYPED_ROUTE_ROLE":
                return {
                    "status": "EXACT_TYPED_ROUTE_ROLE",
                    "required_role": str(direct),
                    "active_positions": theorem_use.get("active_positions"),
                    "authority": auth,
                }
            return {
                "status": "UNAUTHORIZED_DIRECT_ROLE",
                "required_role": None,
                "reason": "required_role without EXACT_TYPED_ROUTE_ROLE authority",
            }

        rs = theorem_use.get("route_semantics") or {}
        if rs.get("schema") != self.ROLE_SCHEMA:
            return {
                "status": "NEED_TYPED_ROUTE_ROLE_CONTRACT",
                "required_role": None,
            }
        if rs.get("status") != "EXACT_TYPED_ROUTE_ROLE":
            return {
                "status": "ROUTE_ROLE_NOT_EXACT",
                "required_role": None,
            }
        role = rs.get("required_role")
        if not role:
            return {
                "status": "ROUTE_ROLE_CONTRACT_INCOMPLETE",
                "required_role": None,
            }
        return {
            "status": "EXACT_TYPED_ROUTE_ROLE",
            "required_role": str(role),
            "active_positions": rs.get("active_positions"),
            "authority": {
                "provider": rs.get("provider"),
                "contract_id": rs.get("contract_id"),
                "provenance": rs.get("provenance"),
                "status": rs.get("status"),
            },
        }

    def emit_from_verified_edge(
        self,
        *,
        root_problem_id: str,
        edge: Dict[str, Any],
        edge_receipt: Dict[str, Any],
        route_occurrence_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if edge_receipt.get("pass") is not True:
            return {
                "status": "NO_EVENT_UNVERIFIED_PROOF_EDGE",
                "event": None,
            }
        use = edge.get("theorem_use")
        if not isinstance(use, dict):
            return {
                "status": "NO_EVENT_NO_THEOREM_USE_DECLARATION",
                "event": None,
            }
        theorem_id = use.get("theorem_id")
        authority = use.get("theorem_authority_id")
        step = use.get("route_step_index")
        provenance = use.get("route_provenance")
        if not theorem_id or not authority or step is None or not provenance:
            return {
                "status": "NO_EVENT_INCOMPLETE_THEOREM_USE_DECLARATION",
                "event": None,
                "missing": [
                    k for k, v in {
                        "theorem_id": theorem_id,
                        "theorem_authority_id": authority,
                        "route_step_index": step,
                        "route_provenance": provenance,
                    }.items() if v in (None, "", [])
                ],
            }
        role = self.adapt_role(use)
        rid = route_occurrence_id or use.get("route_occurrence_id")
        if not rid:
            seed = {
                "root_problem_id": root_problem_id,
                "edge_id": edge_receipt.get("edge_id"),
                "theorem_id": theorem_id,
                "route_step_index": step,
                "route_provenance": provenance,
            }
            rid = "R::PROBLEM_APPLICATION::" + _digest(seed)[:24]

        event = {
            "schema": self.EVENT_SCHEMA,
            "occurrence_scope": "PROBLEM_APPLICATION",
            "root_problem_id": str(root_problem_id),
            "route_occurrence_id": str(rid),
            "theorem_id": str(theorem_id),
            "theorem_authority_id": str(authority),
            "route_step_index": int(step),
            "route_provenance": provenance,
            "required_role": role.get("required_role"),
            "active_positions": role.get("active_positions"),
            "role_adapter_status": role.get("status"),
            "role_authority": role.get("authority"),
            "proof_edge_id": edge_receipt.get("edge_id"),
            "proof_edge_receipt_digest": _digest(edge_receipt),
            "address_credit": "ZERO_UNTIL_PASS050_BINDING",
        }
        event["event_id"] = "THEOREM_USE::" + _digest(event)[:24]
        missing = [k for k in self.REQUIRED if event.get(k) in (None, "", [])]
        event["validation"] = {
            "status": "COMPLETE_PROBLEM_APPLICATION_THEOREM_USE_EVENT" if not missing else "INCOMPLETE_PROBLEM_APPLICATION_THEOREM_USE_EVENT",
            "missing_fields": missing,
            "PASS050_bindable": not missing,
        }
        return {
            "status": "EVENT_EMITTED" if not missing else "EVENT_EMITTED_INCOMPLETE_ROLE",
            "event": event,
        }

    def instrument_reconstruction(
        self,
        *,
        root_problem_id: str,
        edges: Iterable[Dict[str, Any]],
        edge_receipts: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        by_id = {str(r.get("edge_id")): r for r in edge_receipts}
        emitted: List[Dict[str, Any]] = []
        diagnostics: List[Dict[str, Any]] = []
        for edge in edges:
            eid = str(edge.get("id") or _digest(edge))
            receipt = by_id.get(eid)
            if receipt is None:
                diagnostics.append({"edge_id": eid, "status": "NO_EDGE_RECEIPT"})
                continue
            out = self.emit_from_verified_edge(root_problem_id=root_problem_id, edge=edge, edge_receipt=receipt)
            diagnostics.append({"edge_id": eid, "status": out["status"]})
            if out.get("event"):
                emitted.append(out["event"])
        ids = [e["event_id"] for e in emitted]
        return {
            "schema": "THEOREM_USE_EVENT_INSTRUMENTATION_RECEIPT_V1",
            "root_problem_id": root_problem_id,
            "event_count": len(emitted),
            "unique_event_id_count": len(set(ids)),
            "events": emitted,
            "diagnostics": diagnostics,
            "candidate_search_emits_events": False,
            "rule": "Only verified proof applications carrying an explicit theorem_use declaration may emit THEOREM_USE_EVENT; search candidates never emit.",
        }
