from __future__ import annotations

from core.state_flow_event import StateFlowEvent, append_state_flow_event


TestStateEvent = StateFlowEvent
append_test_state_event = append_state_flow_event

__all__ = ["TestStateEvent", "append_test_state_event"]
