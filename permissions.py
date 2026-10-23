"""Request-scoped authorization for the application's two network tools.

This is a boundary between trusted application code and model-directed work,
not an operating-system sandbox. Python code in this process remains trusted.
Reservations are atomic; revocation blocks future starts, not in-flight calls.
"""

from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from time import monotonic
from types import MappingProxyType
from typing import TypeVar
from uuid import UUID, uuid4


SEARCH_RESOURCE = "https://api.deepseek.com/v1/tools/search"
MODEL_RESOURCE = "https://api.deepseek.com/chat/completions"
T = TypeVar("T")


@dataclass(frozen=True)
class _ToolPolicy:
    resource: str
    resource_name: str
    data_class: str
    layer: str


# There is no runtime registration or message-based grant API. Unregistered
# external actions (L2) and administration (L3) are denied by default.
_TOOLS = MappingProxyType({
    "web.search": _ToolPolicy(SEARCH_RESOURCE, "deepseek_search", "public_topic", "L0"),
    "model.complete": _ToolPolicy(MODEL_RESOURCE, "deepseek_model", "conversation", "L1"),
})
_ROLES = MappingProxyType({
    "orchestrator": frozenset(_TOOLS),
    "research": frozenset({"web.search"}),
    "writer": frozenset({"model.complete"}),
    "planner": frozenset({"model.complete"}),
})
_DENIALS = frozenset({
    "not_authorized", "unknown_tool", "resource_mismatch", "data_class_mismatch",
    "not_granted", "budget_exhausted", "expired", "revoked", "closed",
    "invalid_operation", "invalid_grant",
})
_STATUSES = frozenset({
    "issued", "delegated", "allowed", "succeeded", "failed", "denied", "revoked", "closed",
})
_REASONS = _DENIALS | {"granted", "completed", "operation_failed"}


class PermissionDenied(RuntimeError):
    """A safe, fixed explanation suitable for UI handling, with no raw inputs."""

    def __init__(self, reason: str = "not_authorized") -> None:
        self.reason = reason if type(reason) is str and reason in _DENIALS else "not_authorized"
        super().__init__("The requested action is not authorized (" + self.reason + ").")


def _bounded_int(value: object, maximum: int, *, minimum: int = 0) -> int:
    # bool is an int subclass and must not silently become an authorization.
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("Permission limits must be integers within application bounds.")
    return value


def _safe_id(value: object) -> str:
    if type(value) is str and len(value) in (32, 36):
        try:
            return str(UUID(value))
        except ValueError:
            pass
    return str(uuid4())


def _enum(value: object, allowed: object, fallback: str = "unregistered") -> str:
    return value if type(value) is str and value in allowed else fallback


class AuditTrail:
    """Bounded, memory-only metadata. Never stores payloads or exception text."""

    def __init__(self, max_records: int = 200) -> None:
        self._limit = _bounded_int(max_records, 200, minimum=1)
        self._records: deque[dict] = deque(maxlen=self._limit)
        self._lock = RLock()

    def _append(self, *, request_id: str, principal: str, tool: object = "scope",
                resource: object = None, data_class: object = None,
                status: str, reason: str) -> None:
        policy = _TOOLS.get(tool) if type(tool) is str else None
        resource_name = next((item.resource_name for item in _TOOLS.values()
                              if type(resource) is str and resource == item.resource), "unregistered")
        # Values are selected from fixed vocabularies, including rejected input.
        record = {
            "event_id": str(uuid4()),
            "request_id": _safe_id(request_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "principal": _enum(principal, _ROLES),
            "tool": _enum(tool, {*_TOOLS, "scope"}),
            "layer": policy.layer if policy else "control" if tool == "scope" else "unregistered",
            "resource": resource_name,
            "data_class": _enum(data_class, {"public_topic", "conversation"}),
            "status": _enum(status, _STATUSES),
            "reason": _enum(reason, _REASONS),
        }
        with self._lock:
            self._records.append(record)

    def to_records(self) -> list[dict]:
        """Return copies, so a UI cannot alter the retained events."""
        with self._lock:
            return [dict(record) for record in self._records]


@dataclass
class _Scope:
    principal: str
    tools: frozenset[str]
    limits: dict[str, int]
    parent: "_Scope | None" = None
    used: dict[str, int] = field(default_factory=lambda: dict.fromkeys(_TOOLS, 0))
    revoked: bool = False
    closed: bool = False


@dataclass
class _RequestState:
    request_id: str
    deadline: float
    audit: AuditTrail
    lock: object = field(default_factory=RLock)


class PermissionGateway:
    """A server-issued capability with fixed destinations and shared budgets."""

    __slots__ = ("_state", "_scope")

    def __init__(self, request_id: str | None = None, *, search_enabled: bool = True,
                 search_limit: int = 2, model_limit: int = 1,
                 lifetime_seconds: int = 600, audit: AuditTrail | None = None) -> None:
        if type(search_enabled) is not bool:
            raise ValueError("Search permission must be a boolean.")
        search_limit = _bounded_int(search_limit, 2)
        model_limit = _bounded_int(model_limit, 2)
        lifetime_seconds = _bounded_int(lifetime_seconds, 600, minimum=1)
        if audit is not None and type(audit) is not AuditTrail:
            raise ValueError("Use an application-issued audit trail.")
        limits = {"web.search": search_limit if search_enabled else 0,
                  "model.complete": model_limit}
        tools = frozenset(tool for tool, limit in limits.items() if limit)
        self._scope = _Scope("orchestrator", tools, limits)
        self._state = _RequestState(_safe_id(request_id), monotonic() + lifetime_seconds,
                                    audit if audit is not None else AuditTrail())
        self._record(status="issued", reason="granted")

    @property
    def audit(self) -> AuditTrail:
        return self._state.audit

    @property
    def request_id(self) -> str:
        return self._state.request_id

    def _ancestors(self):
        scope = self._scope
        while scope is not None:
            yield scope
            scope = scope.parent

    def _inactive_reason(self) -> str | None:
        scopes = list(self._ancestors())
        if any(scope.revoked for scope in scopes):
            return "revoked"
        if any(scope.closed for scope in scopes):
            return "closed"
        if monotonic() >= self._state.deadline:
            return "expired"
        return None

    def _remaining(self, tool: str) -> int:
        return max(0, min(scope.limits[tool] - scope.used[tool] for scope in self._ancestors()))

    def _record(self, *, status: str, reason: str, tool: object = "scope",
                resource: object = None, data_class: object = None) -> None:
        self.audit._append(request_id=self.request_id, principal=self._scope.principal,
                           status=status, reason=reason, tool=tool,
                           resource=resource, data_class=data_class)

    def _deny(self, reason: str, *, tool: object = "scope", resource: object = None,
              data_class: object = None) -> None:
        self._record(status="denied", reason=reason, tool=tool,
                     resource=resource, data_class=data_class)
        raise PermissionDenied(reason)

    def run(self, tool: str, *, resource: str, data_class: str,
            operation: Callable[[], T]) -> T:
        """Validate and reserve before invoking any transport or side effect."""
        with self._state.lock:
            if reason := self._inactive_reason():
                self._deny(reason, tool=tool, resource=resource, data_class=data_class)
            policy = _TOOLS.get(tool) if type(tool) is str else None
            if policy is None:
                self._deny("unknown_tool", tool=tool, resource=resource, data_class=data_class)
            if type(resource) is not str or resource != policy.resource:
                self._deny("resource_mismatch", tool=tool, resource=resource, data_class=data_class)
            if type(data_class) is not str or data_class != policy.data_class:
                self._deny("data_class_mismatch", tool=tool, resource=resource, data_class=data_class)
            if any(tool not in scope.tools for scope in self._ancestors()):
                self._deny("not_granted", tool=tool, resource=resource, data_class=data_class)
            if self._remaining(tool) == 0:
                self._deny("budget_exhausted", tool=tool, resource=resource, data_class=data_class)
            if not callable(operation):
                self._deny("invalid_operation", tool=tool, resource=resource, data_class=data_class)
            # Reserve under one lock across every ancestor. Failure still costs
            # a call; siblings and grandchildren cannot mint additional budget.
            for scope in self._ancestors():
                scope.used[tool] += 1
            self._record(status="allowed", reason="granted", tool=tool,
                         resource=resource, data_class=data_class)
        try:
            result = operation()
        except BaseException:
            self._record(status="failed", reason="operation_failed", tool=tool,
                         resource=resource, data_class=data_class)
            raise
        self._record(status="succeeded", reason="completed", tool=tool,
                     resource=resource, data_class=data_class)
        return result

    def delegate(self, principal: str, *, tools: Sequence[str] | None = None,
                 search_limit: int | None = None, model_limit: int | None = None) -> "PermissionGateway":
        """Only attenuate a role and its ancestor's remaining authority."""
        with self._state.lock:
            if reason := self._inactive_reason():
                self._deny(reason)
            role = _ROLES.get(principal) if type(principal) is str else None
            if role is None or principal == "orchestrator":
                self._deny("invalid_grant")
            if tools is None:
                selected = self._scope.tools & role
            elif type(tools) not in (tuple, list) or any(type(tool) is not str for tool in tools):
                self._deny("invalid_grant")
            else:
                selected = frozenset(tools)
            if not selected <= (self._scope.tools & role):
                self._deny("invalid_grant")
            limits = {}
            for tool, requested in (("web.search", search_limit), ("model.complete", model_limit)):
                remaining = self._remaining(tool) if tool in selected else 0
                if requested is None:
                    limits[tool] = remaining
                elif type(requested) is not int or not 0 <= requested <= remaining:
                    self._deny("invalid_grant")
                else:
                    limits[tool] = requested
            child = object.__new__(PermissionGateway)
            child._state = self._state
            child._scope = _Scope(principal, selected, limits, parent=self._scope)
            child._record(status="delegated", reason="granted")
            return child

    def revoke(self) -> None:
        """Block new operations in this scope and every descendant."""
        with self._state.lock:
            if not self._scope.revoked:
                self._scope.revoked = True
                self._record(status="revoked", reason="revoked")

    def close(self) -> None:
        """Close a completed scope; already reserved operations may finish."""
        with self._state.lock:
            if not self._scope.closed:
                self._scope.closed = True
                self._record(status="closed", reason="closed")

    def snapshot(self) -> dict:
        """Return sanitized per-request counts, not money or token estimates."""
        with self._state.lock:
            ancestors = list(self._ancestors())
            root = ancestors[-1]
            inactive = self._inactive_reason()
            remaining = {tool: self._remaining(tool) for tool in _TOOLS}
            return {
                "request_id": self.request_id,
                "principal": self._scope.principal,
                "tools": sorted(self._scope.tools),
                "active": inactive is None and any(remaining.values()),
                "revoked": any(scope.revoked for scope in ancestors),
                "closed": any(scope.closed for scope in ancestors),
                "expired": monotonic() >= self._state.deadline,
                "seconds_remaining": max(0, int(self._state.deadline - monotonic())),
                "search_limit": self._scope.limits["web.search"],
                "search_used": root.used["web.search"],
                "search_remaining": remaining["web.search"],
                "model_limit": self._scope.limits["model.complete"],
                "model_used": root.used["model.complete"],
                "model_remaining": remaining["model.complete"],
            }
