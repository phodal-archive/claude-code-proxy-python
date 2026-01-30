"""
Dashboard and metrics endpoints for the Claude Code Proxy service.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Dict, List, Any
import json

from src.core.metrics import get_metrics_service

dashboard_router = APIRouter(prefix="/metrics", tags=["metrics"])


@dashboard_router.get("", response_class=HTMLResponse)
async def dashboard():
    """Render the metrics dashboard HTML page."""
    return get_dashboard_html()


@dashboard_router.get("/api/summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """Get aggregated metrics summary."""
    metrics_service = get_metrics_service()
    return metrics_service.get_aggregated_metrics()


@dashboard_router.get("/api/users")
async def get_user_metrics() -> List[Dict[str, Any]]:
    """Get metrics for all users."""
    metrics_service = get_metrics_service()
    user_metrics = metrics_service.get_user_metrics()
    
    result = []
    for user_id, metrics in user_metrics.items():
        result.append({
            'user_id': user_id,
            'total_requests': metrics['total_requests'],
            'total_tool_calls': metrics['total_tool_calls'],
            'edit_tool_calls': metrics['edit_tool_calls'],
            'lines_modified': metrics['lines_modified'],
            'input_tokens': metrics['input_tokens'],
            'output_tokens': metrics['output_tokens'],
            'first_seen': metrics['first_seen'].isoformat() if metrics['first_seen'] else None,
            'last_seen': metrics['last_seen'].isoformat() if metrics['last_seen'] else None,
            'tool_calls_by_name': dict(metrics.get('tool_calls_by_name', {})),
        })
    
    return result


@dashboard_router.get("/api/turns")
async def get_recent_turns(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent turns/messages."""
    metrics_service = get_metrics_service()
    turns = metrics_service.get_recent_turns(limit)
    
    return [_turn_to_dict(turn) for turn in turns]


@dashboard_router.get("/api/turns/{turn_id}")
async def get_turn_detail(turn_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific turn."""
    metrics_service = get_metrics_service()
    turn = metrics_service.get_turn_by_id(turn_id)
    
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
    
    return _turn_to_dict(turn, include_full_message=True)


@dashboard_router.get("/api/users/{user_id}/turns")
async def get_turns_by_user(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get turns for a specific user."""
    metrics_service = get_metrics_service()
    turns = metrics_service.get_turns_for_user(user_id, limit)
    
    return [_turn_to_dict(turn) for turn in turns]


@dashboard_router.get("/api/sessions")
async def get_recent_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent sessions."""
    metrics_service = get_metrics_service()
    sessions = metrics_service.get_recent_sessions(limit)
    
    return [_session_to_dict(session) for session in sessions]


@dashboard_router.get("/api/sessions/{session_id}/turns")
async def get_turns_by_session(session_id: str) -> List[Dict[str, Any]]:
    """Get turns for a specific session."""
    metrics_service = get_metrics_service()
    turns = metrics_service.get_turns_for_session(session_id)
    
    return [_turn_to_dict(turn) for turn in turns]


@dashboard_router.get("/api/users/{user_id}/sessions")
async def get_sessions_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get sessions for a specific user."""
    metrics_service = get_metrics_service()
    sessions = metrics_service.get_sessions_for_user(user_id)
    
    return [_session_to_dict(session) for session in sessions]


def _turn_to_dict(turn, include_full_message: bool = False) -> Dict[str, Any]:
    """Convert a TurnLog to a dictionary."""
    result = {
        'turn_id': turn.turn_id,
        'user_id': turn.user_id,
        'session_id': turn.session_id,
        'timestamp': datetime.fromtimestamp(turn.timestamp).isoformat(),
        'model': turn.model,
        'stream': turn.stream,
        'tools_offered_count': turn.tools_offered_count,
        'last_user_message_preview': turn.last_user_message_preview,
        'prompt_tokens': turn.prompt_tokens,
        'completion_tokens': turn.completion_tokens,
        'latency_ms': turn.latency_ms,
        'tool_call_count': turn.tool_call_count,
        'edit_tool_call_count': turn.edit_tool_call_count,
        'lines_modified': turn.lines_modified,
        'lines_added': turn.lines_added,
        'lines_removed': turn.lines_removed,
        'has_error': turn.has_error,
        'error_message': turn.error_message,
        'tool_calls': [_tool_call_to_dict(tc) for tc in turn.tool_calls],
    }
    
    if include_full_message:
        result['last_user_message'] = turn.last_user_message
    
    return result


def _tool_call_to_dict(tool_call) -> Dict[str, Any]:
    """Convert a ToolCallLog to a dictionary."""
    return {
        'tool_call_id': tool_call.tool_call_id,
        'turn_id': tool_call.turn_id,
        'name': tool_call.name,
        'args_preview': tool_call.args_preview,
        'timestamp': datetime.fromtimestamp(tool_call.timestamp).isoformat(),
        'duration_ms': tool_call.duration_ms,
        'status': tool_call.status,
        'lines_modified': tool_call.lines_modified,
        'lines_added': tool_call.lines_added,
        'lines_removed': tool_call.lines_removed,
        'file_path': tool_call.file_path,
        'error_message': tool_call.error_message,
    }


def _session_to_dict(session) -> Dict[str, Any]:
    """Convert a SessionInfo to a dictionary."""
    return {
        'session_id': session.session_id,
        'user_id': session.user_id,
        'start_time': datetime.fromtimestamp(session.start_time).isoformat(),
        'last_activity_time': datetime.fromtimestamp(session.last_activity_time).isoformat(),
        'turn_count': session.turn_count,
        'total_tool_calls': session.total_tool_calls,
        'edit_tool_calls': session.edit_tool_calls,
        'total_lines_modified': session.total_lines_modified,
        'total_prompt_tokens': session.total_prompt_tokens,
        'total_completion_tokens': session.total_completion_tokens,
        'avg_tool_calls_per_turn': round(session.get_avg_tool_calls_per_turn(), 2),
        'avg_latency_ms': session.get_avg_latency_ms(),
        'error_count': session.error_count,
        'tool_usage': session.tool_usage,
    }


def get_dashboard_html() -> str:
    """Get the dashboard HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Code Metrics Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <style>
        .card {
            @apply bg-white rounded-lg shadow-md p-6;
        }
        .stat-value {
            @apply text-3xl font-bold text-gray-800;
        }
        .stat-label {
            @apply text-sm text-gray-500 uppercase tracking-wide;
        }
        .tab-active {
            @apply border-b-2 border-blue-500 text-blue-600;
        }
        .tab-inactive {
            @apply text-gray-500 hover:text-gray-700;
        }
        .tool-badge {
            @apply px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800;
        }
        .edit-badge {
            @apply px-2 py-1 text-xs rounded-full bg-green-100 text-green-800;
        }
        .error-badge {
            @apply px-2 py-1 text-xs rounded-full bg-red-100 text-red-800;
        }
        .expandable-row {
            cursor: pointer;
        }
        .expandable-row:hover {
            @apply bg-gray-50;
        }
        .tool-call-detail {
            @apply bg-gray-50 border-l-4 border-blue-200;
        }
        .message-preview-cell {
            cursor: help;
        }
        .message-full-tooltip {
            display: none;
            position: fixed;
            z-index: 9999;
            background: white;
            border: 1px solid #d1d5db;
            border-radius: 0.5rem;
            padding: 1rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            max-width: 600px;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.875rem;
            line-height: 1.5;
            color: #374151;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-4xl font-bold text-gray-800">Claude Code Metrics Dashboard</h1>
            <p class="text-gray-600 mt-2">Real-time observability for AI Agent usage - User → Session → Message → ToolCalls</p>
        </header>

        <!-- Summary Stats -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="card">
                <div class="stat-label">Total Requests</div>
                <div class="stat-value" id="stat-requests">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Total Tool Calls</div>
                <div class="stat-value" id="stat-tool-calls">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Edit Tool Calls</div>
                <div class="stat-value text-blue-600" id="stat-edit-calls">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Lines Modified</div>
                <div class="stat-value text-green-600" id="stat-lines">0</div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="card">
                <div class="stat-label">Input Tokens</div>
                <div class="stat-value text-purple-600" id="stat-input-tokens">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Output Tokens</div>
                <div class="stat-value text-orange-600" id="stat-output-tokens">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Active Users</div>
                <div class="stat-value text-indigo-600" id="stat-users">0</div>
            </div>
            <div class="card">
                <div class="stat-label">Avg Tool Calls/Request</div>
                <div class="stat-value" id="stat-avg-calls">0</div>
            </div>
        </div>

        <!-- Tab Navigation -->
        <div class="card mb-8">
            <div class="border-b border-gray-200 mb-4">
                <nav class="-mb-px flex space-x-8">
                    <button onclick="showTab('turns')" id="tab-turns" class="py-2 px-1 tab-active font-medium text-sm">
                        Messages (Turns)
                    </button>
                    <button onclick="showTab('sessions')" id="tab-sessions" class="py-2 px-1 tab-inactive font-medium text-sm">
                        Sessions
                    </button>
                    <button onclick="showTab('users')" id="tab-users" class="py-2 px-1 tab-inactive font-medium text-sm">
                        Users
                    </button>
                    <button onclick="showTab('tools')" id="tab-tools" class="py-2 px-1 tab-inactive font-medium text-sm">
                        Tool Distribution
                    </button>
                </nav>
            </div>
            
            <!-- Turns Tab -->
            <div id="content-turns" class="tab-content">
                <h2 class="text-xl font-semibold mb-4">Recent Messages (with Tool Calls)</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200" id="turns-table">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message Preview</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tool Calls</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Edits/Lines</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tokens</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Latency</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200" id="turns-body">
                            <tr>
                                <td colspan="8" class="px-4 py-4 text-center text-gray-500">Loading...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Sessions Tab -->
            <div id="content-sessions" class="tab-content hidden">
                <h2 class="text-xl font-semibold mb-4">Active Sessions</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200" id="sessions-table">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Session</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Activity</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Turns</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tool Calls</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg TC/Turn</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lines Modified</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Errors</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200" id="sessions-body">
                            <tr>
                                <td colspan="9" class="px-4 py-4 text-center text-gray-500">Loading...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Users Tab -->
            <div id="content-users" class="tab-content hidden">
                <h2 class="text-xl font-semibold mb-4">User Metrics</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User ID</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tool Calls</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Edit Tools</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lines Modified</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Input Tokens</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Output Tokens</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Seen</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200" id="users-body">
                            <tr>
                                <td colspan="8" class="px-6 py-4 text-center text-gray-500">No user data yet</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Tools Tab -->
            <div id="content-tools" class="tab-content hidden">
                <h2 class="text-xl font-semibold mb-4">Tool Calls Distribution</h2>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <canvas id="toolCallsChart" height="400"></canvas>
                    </div>
                    <div>
                        <canvas id="userActivityChart" height="400"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tool Call Detail Modal -->
        <div id="tool-detail-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
            <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold">Tool Call Details</h3>
                        <button onclick="closeModal()" class="text-gray-500 hover:text-gray-700">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div id="modal-content"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let toolCallsData = {};
        let userMetrics = [];
        let chartsInitialized = false;
        
        // Tab switching
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[id^="tab-"]').forEach(el => {
                el.classList.remove('tab-active');
                el.classList.add('tab-inactive');
            });
            
            document.getElementById('content-' + tabName).classList.remove('hidden');
            document.getElementById('tab-' + tabName).classList.remove('tab-inactive');
            document.getElementById('tab-' + tabName).classList.add('tab-active');
            
            if (tabName === 'turns') loadTurns();
            if (tabName === 'sessions') loadSessions();
            if (tabName === 'users') loadUsers();
            if (tabName === 'tools') {
                if (!chartsInitialized) {
                    loadMetricsAndInitCharts();
                }
            }
        }
        
        // Load and display metrics summary
        async function loadMetricsSummary() {
            try {
                const response = await fetch('/metrics/api/summary');
                const metrics = await response.json();
                
                document.getElementById('stat-requests').textContent = metrics.total_requests;
                document.getElementById('stat-tool-calls').textContent = metrics.total_tool_calls;
                document.getElementById('stat-edit-calls').textContent = metrics.total_edit_tool_calls;
                document.getElementById('stat-lines').textContent = metrics.total_lines_modified;
                document.getElementById('stat-input-tokens').textContent = metrics.total_input_tokens;
                document.getElementById('stat-output-tokens').textContent = metrics.total_output_tokens;
                document.getElementById('stat-users').textContent = metrics.active_users;
                document.getElementById('stat-avg-calls').textContent = metrics.avg_tool_calls_per_request.toFixed(2);
                
                toolCallsData = metrics.tool_calls_by_name;
            } catch (e) {
                console.error('Failed to load metrics summary:', e);
            }
        }
        
        // Load turns data
        async function loadTurns() {
            try {
                const response = await fetch('/metrics/api/turns');
                const turns = await response.json();
                renderTurns(turns);
            } catch (e) {
                console.error('Failed to load turns:', e);
            }
        }
        
        function renderTurns(turns) {
            const tbody = document.getElementById('turns-body');
            if (turns.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="px-4 py-4 text-center text-gray-500">No messages yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = turns.map(turn => `
                <tr class="expandable-row" onclick="toggleTurnDetail('${turn.turn_id}')">
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${formatTime(turn.timestamp)}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">${truncate(turn.user_id, 15)}</td>
                    <td class="px-4 py-3 text-sm text-gray-500 max-w-xs">
                        <div class="message-preview-cell" data-turn-id="${turn.turn_id}" data-preview-message="${escapeHtml(turn.last_user_message_preview || '')}">${escapeHtml(truncate(turn.last_user_message_preview || '-', 50))}</div>
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${turn.model || '-'}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm">
                        ${turn.tool_call_count > 0 ? '<span class="tool-badge">' + turn.tool_call_count + ' calls</span>' : '<span class="text-gray-400">-</span>'}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm">
                        ${turn.edit_tool_call_count > 0 ? '<span class="edit-badge">' + turn.edit_tool_call_count + ' edits</span> <span class="text-green-600">+' + (turn.lines_added || 0) + '</span> <span class="text-red-600">-' + (turn.lines_removed || 0) + '</span>' : '<span class="text-gray-400">-</span>'}
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${turn.prompt_tokens || 0} / ${turn.completion_tokens || 0}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${turn.latency_ms ? turn.latency_ms + 'ms' : '-'}</td>
                </tr>
                <tr id="detail-${turn.turn_id}" class="hidden tool-call-detail">
                    <td colspan="8" class="px-4 py-3">
                        ${renderToolCalls(turn.tool_calls || [])}
                    </td>
                </tr>
            `).join('');
        }
        
        function renderToolCalls(toolCalls) {
            if (toolCalls.length === 0) {
                return '<div class="text-gray-500 text-sm">No tool calls in this message</div>';
            }
            
            return '<div class="space-y-2"><div class="font-medium text-sm text-gray-700">Tool Calls:</div>' +
                toolCalls.map(tc => `
                    <div class="bg-white p-3 rounded border border-gray-200">
                        <div class="flex items-center justify-between">
                            <div>
                                <span class="font-medium text-sm">${tc.name}</span>
                                ${tc.file_path ? '<span class="ml-2 text-xs text-gray-500 font-mono">' + truncate(tc.file_path, 40) + '</span>' : ''}
                            </div>
                            <div class="flex items-center space-x-2">
                                ${(tc.lines_added > 0 || tc.lines_removed > 0) ? '<span class="text-xs"><span class="text-green-600 font-medium">+' + (tc.lines_added || 0) + '</span><span class="text-red-600 font-medium">-' + (tc.lines_removed || 0) + '</span></span>' : ''}
                                <span class="text-xs px-2 py-0.5 rounded ${tc.status === 'ok' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">${tc.status}</span>
                            </div>
                        </div>
                        ${tc.args_preview ? '<div class="mt-1 text-xs text-gray-600 font-mono bg-gray-50 p-2 rounded overflow-x-auto">' + escapeHtml(tc.args_preview) + '</div>' : ''}
                    </div>
                `).join('') + '</div>';
        }
        
        function toggleTurnDetail(turnId) {
            const detailRow = document.getElementById('detail-' + turnId);
            if (detailRow) {
                detailRow.classList.toggle('hidden');
            }
        }
        
        // Load sessions data
        async function loadSessions() {
            try {
                const response = await fetch('/metrics/api/sessions');
                const sessions = await response.json();
                renderSessions(sessions);
            } catch (e) {
                console.error('Failed to load sessions:', e);
            }
        }
        
        function renderSessions(sessions) {
            const tbody = document.getElementById('sessions-body');
            if (sessions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="px-4 py-4 text-center text-gray-500">No sessions yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = sessions.map(s => `
                <tr class="expandable-row" onclick="loadSessionTurns('${s.session_id}')">
                    <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-blue-600">${truncate(s.session_id, 20)}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">${truncate(s.user_id, 15)}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${formatTime(s.start_time)}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${formatTime(s.last_activity_time)}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${s.turn_count}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${s.total_tool_calls}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">${s.avg_tool_calls_per_turn.toFixed(1)}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm text-green-600">${s.total_lines_modified}</td>
                    <td class="px-4 py-3 whitespace-nowrap text-sm">
                        ${s.error_count > 0 ? '<span class="error-badge">' + s.error_count + '</span>' : '<span class="text-gray-400">0</span>'}
                    </td>
                </tr>
            `).join('');
        }
        
        async function loadSessionTurns(sessionId) {
            try {
                const response = await fetch(`/metrics/api/sessions/${sessionId}/turns`);
                const turns = await response.json();
                showModal(sessionId, turns);
            } catch (e) {
                console.error('Failed to load session turns:', e);
            }
        }
        
        // Load users data
        async function loadUsers() {
            try {
                const response = await fetch('/metrics/api/users');
                const users = await response.json();
                renderUsers(users);
            } catch (e) {
                console.error('Failed to load users:', e);
            }
        }
        
        function renderUsers(users) {
            const tbody = document.getElementById('users-body');
            if (users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-gray-500">No user data yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        <a href="#" class="text-blue-600 hover:underline">${escapeHtml(user.user_id)}</a>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${user.total_requests}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${user.total_tool_calls}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-blue-600">${user.edit_tool_calls}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600">${user.lines_modified}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-purple-600">${user.input_tokens}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-orange-600">${user.output_tokens}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${user.last_seen ? formatDateTime(user.last_seen) : '-'}</td>
                </tr>
            `).join('');
            
            userMetrics = users;
        }
        
        function showModal(sessionId, turns) {
            const modal = document.getElementById('tool-detail-modal');
            const content = document.getElementById('modal-content');
            
            content.innerHTML = `
                <div class="mb-4">
                    <span class="text-sm text-gray-500">Session:</span>
                    <span class="font-mono text-sm">${sessionId}</span>
                </div>
                <div class="space-y-4">
                    ${turns.length === 0 ? '<div class="text-gray-500">No messages in this session</div>' : turns.map(turn => `
                        <div class="border border-gray-200 rounded-lg p-4">
                            <div class="flex justify-between items-start mb-2">
                                <div>
                                    <span class="text-sm text-gray-500">${formatTime(turn.timestamp)}</span>
                                    <span class="ml-2 text-sm font-medium">${turn.model || 'unknown'}</span>
                                </div>
                                <div class="flex items-center space-x-2">
                                    ${turn.tool_call_count > 0 ? '<span class="tool-badge">' + turn.tool_call_count + ' tool calls</span>' : ''}
                                    ${turn.has_error ? '<span class="error-badge">Error</span>' : ''}
                                </div>
                            </div>
                            <div class="text-sm text-gray-700 mb-2">${escapeHtml(turn.last_user_message_preview || 'No message preview')}</div>
                            ${turn.tool_calls && turn.tool_calls.length > 0 ? '<div class="mt-3 border-t pt-3">' + renderToolCalls(turn.tool_calls) + '</div>' : ''}
                        </div>
                    `).join('')}
                </div>
            `;
            
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
        
        function closeModal() {
            const modal = document.getElementById('tool-detail-modal');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        
        // Utility functions
        function formatTime(timestamp) {
            if (!timestamp) return '-';
            const date = new Date(timestamp);
            return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }
        
        function formatDateTime(timestamp) {
            if (!timestamp) return '-';
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US') + ' ' + date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        }
        
        function truncate(str, len) {
            if (!str) return '-';
            return str.length > len ? str.substring(0, len) + '...' : str;
        }
        
        function escapeHtml(str) {
            if (!str) return '';
            return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }
        
        // Load metrics and initialize charts
        async function loadMetricsAndInitCharts() {
            await loadMetricsSummary();
            await loadUsers();
            initCharts();
        }
        
        // Initialize charts
        function initCharts() {
            const toolCallsCtx = document.getElementById('toolCallsChart');
            const userActivityCtx = document.getElementById('userActivityChart');
            
            if (!toolCallsCtx || !userActivityCtx) return;
            
            const toolLabels = Object.keys(toolCallsData);
            const toolValues = Object.values(toolCallsData);
            
            new Chart(toolCallsCtx, {
                type: 'bar',
                data: {
                    labels: toolLabels,
                    datasets: [{
                        label: 'Tool Calls',
                        data: toolValues,
                        backgroundColor: 'rgba(59, 130, 246, 0.5)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });
            
            const userLabels = userMetrics.map(u => truncate(u.user_id, 15));
            const userRequests = userMetrics.map(u => u.total_requests);
            const userToolCalls = userMetrics.map(u => u.total_tool_calls);
            
            new Chart(userActivityCtx, {
                type: 'bar',
                data: {
                    labels: userLabels,
                    datasets: [
                        {
                            label: 'Requests',
                            data: userRequests,
                            backgroundColor: 'rgba(99, 102, 241, 0.5)',
                            borderColor: 'rgba(99, 102, 241, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Tool Calls',
                            data: userToolCalls,
                            backgroundColor: 'rgba(34, 197, 94, 0.5)',
                            borderColor: 'rgba(34, 197, 94, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top' } },
                    scales: { y: { beginAtZero: true } }
                }
            });
            
            chartsInitialized = true;
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadMetricsSummary();
            loadTurns();
            
            // Setup tooltip for message preview
            const $tooltip = $('<div class="message-full-tooltip"></div>').appendTo('body');
            const fullMessageCache = new Map();

            $(document).on('mouseenter', '.message-preview-cell', function(e) {
                const $cell = $(this);
                const turnId = $cell.data('turn-id');
                const previewMessage = $cell.data('preview-message');

                if (!turnId) {
                    if (previewMessage && previewMessage !== '-') {
                        $tooltip.text(previewMessage).show();
                        positionTooltip(e);
                    }
                    return;
                }

                const cached = fullMessageCache.get(turnId);
                if (cached) {
                    $tooltip.text(cached).show();
                    positionTooltip(e);
                    return;
                }

                if (previewMessage && previewMessage !== '-') {
                    $tooltip.text(previewMessage).show();
                    positionTooltip(e);
                }

                fetch(`/metrics/api/turns/${encodeURIComponent(turnId)}`)
                    .then(r => r.json())
                    .then(data => {
                        const full = (data && data.last_user_message) ? String(data.last_user_message) : null;
                        if (full && full.trim().length > 0) {
                            fullMessageCache.set(turnId, full);
                            if ($cell.is(':hover')) {
                                $tooltip.text(full).show();
                            }
                        }
                    })
                    .catch(() => {});
            });

            $(document).on('mousemove', '.message-preview-cell', function(e) {
                if ($tooltip.is(':visible')) {
                    positionTooltip(e);
                }
            });

            $(document).on('mouseleave', '.message-preview-cell', function() {
                $tooltip.hide();
            });

            function positionTooltip(e) {
                const tooltipWidth = $tooltip.outerWidth();
                const tooltipHeight = $tooltip.outerHeight();
                const windowWidth = $(window).width();
                const windowHeight = $(window).height();

                let left = e.pageX + 15;
                let top = e.pageY + 15;

                if (left + tooltipWidth > windowWidth) {
                    left = e.pageX - tooltipWidth - 15;
                }

                if (top + tooltipHeight > windowHeight + $(window).scrollTop()) {
                    top = e.pageY - tooltipHeight - 15;
                }

                $tooltip.css({ left: left + 'px', top: top + 'px' });
            }
        });
        
        // Auto-refresh every 10 seconds
        setInterval(() => {
            const activeTab = document.querySelector('.tab-active')?.id.replace('tab-', '');
            if (activeTab === 'turns') {
                loadMetricsSummary();
                loadTurns();
            }
            if (activeTab === 'sessions') loadSessions();
        }, 10000);
        
        // Close modal on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeModal();
        });
    </script>
</body>
</html>"""
