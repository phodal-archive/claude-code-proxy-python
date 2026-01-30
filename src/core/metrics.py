"""
Metrics collection and aggregation for the Claude Code Proxy service.
"""
from datetime import datetime
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import time


@dataclass
class ToolCallLog:
    """Log entry for a single tool call."""
    tool_call_id: str
    turn_id: str
    name: str
    args_preview: str = ""
    timestamp: float = field(default_factory=time.time)
    duration_ms: int = 0
    status: str = "ok"
    lines_modified: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    file_path: str = ""
    error_message: str = ""


@dataclass
class TurnLog:
    """Log entry for a single turn (message exchange)."""
    turn_id: str
    user_id: str
    session_id: str
    timestamp: float = field(default_factory=time.time)
    model: str = ""
    stream: bool = False
    tools_offered_count: int = 0
    last_user_message_preview: str = ""
    last_user_message: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    tool_call_count: int = 0
    edit_tool_call_count: int = 0
    lines_modified: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    has_error: bool = False
    error_message: str = ""
    tool_calls: List[ToolCallLog] = field(default_factory=list)


@dataclass
class SessionInfo:
    """Information about an active session."""
    session_id: str
    user_id: str
    start_time: float = field(default_factory=time.time)
    last_activity_time: float = field(default_factory=time.time)
    turn_count: int = 0
    total_tool_calls: int = 0
    edit_tool_calls: int = 0
    total_lines_modified: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    error_count: int = 0
    tool_usage: Dict[str, int] = field(default_factory=dict)

    def get_avg_tool_calls_per_turn(self) -> float:
        if self.turn_count == 0:
            return 0
        return self.total_tool_calls / self.turn_count

    def get_avg_latency_ms(self) -> float:
        # This would need to be calculated from turn logs
        return 0


class MetricsService:
    """Service for collecting and aggregating metrics."""

    def __init__(self, max_recent_turns: int = 1000, max_recent_requests: int = 100):
        self.max_recent_turns = max_recent_turns
        self.max_recent_requests = max_recent_requests
        
        # Thread-safe data structures
        self._lock = Lock()
        
        # Recent turns (limited FIFO queue)
        self.recent_turns: deque = deque(maxlen=max_recent_turns)
        
        # User metrics
        self.user_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'user_id': '',
            'total_requests': 0,
            'total_tool_calls': 0,
            'edit_tool_calls': 0,
            'lines_modified': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'first_seen': None,
            'last_seen': None,
            'tool_calls_by_name': defaultdict(int),
        })
        
        # Session metrics
        self.sessions: Dict[str, SessionInfo] = {}
        
        # Aggregated metrics
        self.total_requests = 0
        self.total_tool_calls = 0
        self.total_edit_tool_calls = 0
        self.total_lines_modified = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.tool_calls_by_name: Dict[str, int] = defaultdict(int)

    def record_turn(self, turn_log: TurnLog):
        """Record a turn/message exchange."""
        with self._lock:
            self.recent_turns.append(turn_log)
            
            # Update aggregated metrics
            self.total_requests += 1
            self.total_tool_calls += turn_log.tool_call_count
            self.total_edit_tool_calls += turn_log.edit_tool_call_count
            self.total_lines_modified += turn_log.lines_modified
            self.total_input_tokens += turn_log.prompt_tokens
            self.total_output_tokens += turn_log.completion_tokens
            
            # Update tool call distribution
            for tool_call in turn_log.tool_calls:
                self.tool_calls_by_name[tool_call.name] += 1
            
            # Update user metrics
            user_id = turn_log.user_id
            if user_id not in self.user_metrics:
                self.user_metrics[user_id] = {
                    'user_id': user_id,
                    'total_requests': 0,
                    'total_tool_calls': 0,
                    'edit_tool_calls': 0,
                    'lines_modified': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'first_seen': datetime.fromtimestamp(turn_log.timestamp),
                    'last_seen': datetime.fromtimestamp(turn_log.timestamp),
                    'tool_calls_by_name': defaultdict(int),
                }
            
            user_metrics = self.user_metrics[user_id]
            user_metrics['total_requests'] += 1
            user_metrics['total_tool_calls'] += turn_log.tool_call_count
            user_metrics['edit_tool_calls'] += turn_log.edit_tool_call_count
            user_metrics['lines_modified'] += turn_log.lines_modified
            user_metrics['input_tokens'] += turn_log.prompt_tokens
            user_metrics['output_tokens'] += turn_log.completion_tokens
            user_metrics['last_seen'] = datetime.fromtimestamp(turn_log.timestamp)
            
            for tool_call in turn_log.tool_calls:
                user_metrics['tool_calls_by_name'][tool_call.name] += 1
            
            # Update session metrics
            session_id = turn_log.session_id
            if session_id not in self.sessions:
                self.sessions[session_id] = SessionInfo(
                    session_id=session_id,
                    user_id=user_id,
                    start_time=turn_log.timestamp,
                )
            
            session = self.sessions[session_id]
            session.last_activity_time = turn_log.timestamp
            session.turn_count += 1
            session.total_tool_calls += turn_log.tool_call_count
            session.edit_tool_calls += turn_log.edit_tool_call_count
            session.total_lines_modified += turn_log.lines_modified
            session.total_prompt_tokens += turn_log.prompt_tokens
            session.total_completion_tokens += turn_log.completion_tokens
            
            if turn_log.has_error:
                session.error_count += 1
            
            for tool_call in turn_log.tool_calls:
                session.tool_usage[tool_call.name] = session.tool_usage.get(tool_call.name, 0) + 1

    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics."""
        with self._lock:
            active_users = len(self.user_metrics)
            avg_tool_calls_per_request = (
                self.total_tool_calls / self.total_requests 
                if self.total_requests > 0 
                else 0
            )
            
            return {
                'total_requests': self.total_requests,
                'total_tool_calls': self.total_tool_calls,
                'total_edit_tool_calls': self.total_edit_tool_calls,
                'total_lines_modified': self.total_lines_modified,
                'total_input_tokens': self.total_input_tokens,
                'total_output_tokens': self.total_output_tokens,
                'active_users': active_users,
                'avg_tool_calls_per_request': round(avg_tool_calls_per_request, 2),
                'tool_calls_by_name': dict(self.tool_calls_by_name),
            }

    def get_user_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all users."""
        with self._lock:
            return dict(self.user_metrics)

    def get_recent_turns(self, limit: int = 100) -> List[TurnLog]:
        """Get recent turns."""
        with self._lock:
            # Return in reverse order (most recent first)
            turns = list(self.recent_turns)
            return turns[-limit:][::-1]

    def get_turns_for_user(self, user_id: str, limit: int = 50) -> List[TurnLog]:
        """Get turns for a specific user."""
        with self._lock:
            turns = [t for t in self.recent_turns if t.user_id == user_id]
            return turns[-limit:][::-1]

    def get_turns_for_session(self, session_id: str) -> List[TurnLog]:
        """Get turns for a specific session."""
        with self._lock:
            return [t for t in self.recent_turns if t.session_id == session_id]

    def get_turn_by_id(self, turn_id: str) -> Optional[TurnLog]:
        """Get a specific turn by ID."""
        with self._lock:
            for turn in self.recent_turns:
                if turn.turn_id == turn_id:
                    return turn
            return None

    def get_recent_sessions(self, limit: int = 50) -> List[SessionInfo]:
        """Get recent sessions."""
        with self._lock:
            sessions = sorted(
                self.sessions.values(),
                key=lambda s: s.last_activity_time,
                reverse=True
            )
            return sessions[:limit]

    def get_sessions_for_user(self, user_id: str) -> List[SessionInfo]:
        """Get sessions for a specific user."""
        with self._lock:
            return [s for s in self.sessions.values() if s.user_id == user_id]


# Global metrics service instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get or create the global metrics service."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
