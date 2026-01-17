"""
Wukong Scheduler - DAG-based task graph scheduling

Handles loading track templates, instantiating task graphs,
and determining which nodes are ready for execution based on DAG dependencies.
"""

import json
import uuid
import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass


# Track types
TRACK_TYPES = {"fix", "feature", "refactor", "direct"}

# Node status values
NODE_STATUS = {"pending", "running", "done", "failed", "blocked"}

# Graph status values
GRAPH_STATUS = {"created", "running", "paused", "completed", "aborted"}


@dataclass
class NodeDependency:
    """Represents a dependency between nodes."""
    from_node: str
    to_node: str
    condition: str = "on_success"  # on_success, on_failure, always


class Scheduler:
    """
    Scheduler for Wukong task graph execution.

    Responsibilities:
    - Load track templates from the templates directory
    - Instantiate task graphs from templates
    - Determine which nodes are ready for execution (DAG resolution)
    - Update node statuses

    Example:
        scheduler = Scheduler(Path("~/.wukong/templates"))
        template = scheduler.load_template("fix")
        graph = scheduler.instantiate_graph(template, "Fix the login bug")
        ready_nodes = scheduler.get_ready_nodes(graph)
    """

    def __init__(self, template_dir: Path):
        """
        Initialize the Scheduler.

        Args:
            template_dir: Path to the templates directory
        """
        self.template_dir = Path(template_dir).expanduser()

    def _generate_graph_id(self) -> str:
        """Generate a unique graph ID matching pattern ^tg_[a-z0-9]+$."""
        return f"tg_{uuid.uuid4().hex[:12]}"

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def load_template(self, track: str) -> Dict[str, Any]:
        """
        Load a track template from the templates directory.

        Args:
            track: Track type (fix, feature, refactor, direct)

        Returns:
            Template dictionary

        Raises:
            ValueError: If track is invalid
            FileNotFoundError: If template file doesn't exist
        """
        if track not in TRACK_TYPES:
            raise ValueError(
                f"Invalid track: {track}. "
                f"Must be one of: {sorted(TRACK_TYPES)}"
            )

        template_file = self.template_dir / f"{track}_track.json"

        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_file}")

        with open(template_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def instantiate_graph(
        self,
        template: Dict[str, Any],
        user_prompt: str,
        working_dir: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new task graph instance from a template.

        Args:
            template: Template dictionary (from load_template)
            user_prompt: User's task description
            working_dir: Working directory for execution
            tags: Optional tags for categorization

        Returns:
            New task graph instance with unique ID
        """
        # Deep copy template to avoid mutation
        graph = copy.deepcopy(template)

        # Generate new unique ID
        graph["id"] = self._generate_graph_id()

        # Update timestamps
        now = self._get_timestamp()
        graph["created_at"] = now
        graph["updated_at"] = now

        # Set status to created
        graph["status"] = "created"

        # Update title based on user prompt
        graph["title"] = f"{template.get('track', 'Task').title()}: {user_prompt[:50]}"

        # Set metadata
        if "metadata" not in graph:
            graph["metadata"] = {}
        graph["metadata"]["user_prompt"] = user_prompt
        if tags:
            graph["metadata"]["tags"] = tags

        # Set context
        if "context" not in graph:
            graph["context"] = {}
        if working_dir:
            graph["context"]["working_dir"] = working_dir

        # Initialize execution state
        graph["execution"] = {
            "current_phase": 0,
            "active_nodes": [],
            "completed_nodes": [],
            "failed_nodes": [],
        }

        # Reset all node statuses to pending
        for node in graph.get("nodes", []):
            node["status"] = "pending"
            node["outputs"] = {}

        return graph

    def _get_incoming_edges(
        self,
        graph: Dict[str, Any],
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all edges pointing to a node."""
        return [
            edge for edge in graph.get("edges", [])
            if edge["to"] == node_id
        ]

    def _get_outgoing_edges(
        self,
        graph: Dict[str, Any],
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all edges originating from a node."""
        return [
            edge for edge in graph.get("edges", [])
            if edge["from"] == node_id
        ]

    def _get_node_by_id(
        self,
        graph: Dict[str, Any],
        node_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a node by its ID."""
        for node in graph.get("nodes", []):
            if node["id"] == node_id:
                return node
        return None

    def _is_dependency_satisfied(
        self,
        graph: Dict[str, Any],
        edge: Dict[str, Any],
    ) -> bool:
        """
        Check if a dependency (edge) is satisfied.

        Args:
            graph: Task graph
            edge: Edge defining the dependency

        Returns:
            True if dependency is satisfied
        """
        from_node = self._get_node_by_id(graph, edge["from"])
        if not from_node:
            return False

        from_status = from_node.get("status", "pending")
        condition = edge.get("condition", "on_success")

        if condition == "on_success":
            return from_status == "done"
        elif condition == "on_failure":
            return from_status == "failed"
        elif condition == "always":
            return from_status in ("done", "failed")

        return False

    def get_ready_nodes(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all nodes that are ready for execution.

        A node is ready if:
        1. Its status is "pending"
        2. All incoming dependencies are satisfied
        3. It's not blocked

        Args:
            graph: Task graph

        Returns:
            List of ready node dictionaries
        """
        ready = []

        for node in graph.get("nodes", []):
            # Skip non-pending nodes
            if node.get("status", "pending") != "pending":
                continue

            # Get incoming edges
            incoming = self._get_incoming_edges(graph, node["id"])

            # If no incoming edges, node is ready (root node)
            if not incoming:
                ready.append(node)
                continue

            # Check if all dependencies are satisfied
            all_satisfied = all(
                self._is_dependency_satisfied(graph, edge)
                for edge in incoming
            )

            if all_satisfied:
                ready.append(node)

        return ready

    def mark_node_status(
        self,
        graph: Dict[str, Any],
        node_id: str,
        status: str,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update a node's status in the graph.

        Args:
            graph: Task graph (modified in place)
            node_id: ID of the node to update
            status: New status (pending, running, done, failed, blocked)
            outputs: Optional outputs to set (for done status)
            error: Optional error info (for failed status)

        Returns:
            The updated graph

        Raises:
            ValueError: If status is invalid or node not found
        """
        if status not in NODE_STATUS:
            raise ValueError(
                f"Invalid status: {status}. "
                f"Must be one of: {sorted(NODE_STATUS)}"
            )

        node = self._get_node_by_id(graph, node_id)
        if not node:
            raise ValueError(f"Node not found: {node_id}")

        # Update node status
        node["status"] = status

        # Update outputs if provided
        if outputs and status == "done":
            node["outputs"] = outputs

        # Update error if provided
        if error and status == "failed":
            node["error"] = error

        # Update execution tracking in graph
        execution = graph.get("execution", {})

        # Update active nodes
        active = execution.get("active_nodes", [])
        if status == "running":
            if node_id not in active:
                active.append(node_id)
        else:
            if node_id in active:
                active.remove(node_id)
        execution["active_nodes"] = active

        # Update completed nodes
        completed = execution.get("completed_nodes", [])
        if status == "done" and node_id not in completed:
            completed.append(node_id)
        execution["completed_nodes"] = completed

        # Update failed nodes
        failed = execution.get("failed_nodes", [])
        if status == "failed" and node_id not in failed:
            failed.append(node_id)
        execution["failed_nodes"] = failed

        graph["execution"] = execution
        graph["updated_at"] = self._get_timestamp()

        return graph

    def get_downstream_nodes(
        self,
        graph: Dict[str, Any],
        node_id: str,
    ) -> List[str]:
        """
        Get IDs of all nodes downstream from a given node.

        Args:
            graph: Task graph
            node_id: Source node ID

        Returns:
            List of downstream node IDs
        """
        outgoing = self._get_outgoing_edges(graph, node_id)
        return [edge["to"] for edge in outgoing]

    def get_upstream_nodes(
        self,
        graph: Dict[str, Any],
        node_id: str,
    ) -> List[str]:
        """
        Get IDs of all nodes upstream from a given node.

        Args:
            graph: Task graph
            node_id: Target node ID

        Returns:
            List of upstream node IDs
        """
        incoming = self._get_incoming_edges(graph, node_id)
        return [edge["from"] for edge in incoming]

    def is_graph_complete(self, graph: Dict[str, Any]) -> bool:
        """
        Check if the graph execution is complete.

        A graph is complete if all nodes are either done or failed.

        Args:
            graph: Task graph

        Returns:
            True if execution is complete
        """
        for node in graph.get("nodes", []):
            status = node.get("status", "pending")
            if status not in ("done", "failed"):
                return False
        return True

    def get_graph_status(self, graph: Dict[str, Any]) -> str:
        """
        Determine the overall status of the graph.

        Args:
            graph: Task graph

        Returns:
            Status string: created, running, completed, aborted
        """
        nodes = graph.get("nodes", [])

        if not nodes:
            return "created"

        # Check for any running nodes
        has_running = any(n.get("status") == "running" for n in nodes)
        if has_running:
            return "running"

        # Check for any pending nodes
        has_pending = any(n.get("status") == "pending" for n in nodes)

        # Check for any failed nodes
        has_failed = any(n.get("status") == "failed" for n in nodes)

        if not has_pending:
            # All nodes are done or failed
            if has_failed:
                return "completed"  # Completed with failures
            return "completed"

        # Has pending nodes but nothing running
        if has_failed:
            return "aborted"  # Blocked due to failures

        return "created"  # Initial state

    def get_execution_summary(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of the graph execution state.

        Args:
            graph: Task graph

        Returns:
            Summary dictionary with counts and lists
        """
        nodes = graph.get("nodes", [])

        pending = [n["id"] for n in nodes if n.get("status") == "pending"]
        running = [n["id"] for n in nodes if n.get("status") == "running"]
        done = [n["id"] for n in nodes if n.get("status") == "done"]
        failed = [n["id"] for n in nodes if n.get("status") == "failed"]
        blocked = [n["id"] for n in nodes if n.get("status") == "blocked"]

        return {
            "total_nodes": len(nodes),
            "pending": {"count": len(pending), "nodes": pending},
            "running": {"count": len(running), "nodes": running},
            "done": {"count": len(done), "nodes": done},
            "failed": {"count": len(failed), "nodes": failed},
            "blocked": {"count": len(blocked), "nodes": blocked},
            "progress_percent": (len(done) / len(nodes) * 100) if nodes else 0,
            "status": self.get_graph_status(graph),
        }

    def topological_sort(self, graph: Dict[str, Any]) -> List[str]:
        """
        Return nodes in topological order (respecting dependencies).

        Uses Kahn's algorithm for topological sorting.

        Args:
            graph: Task graph

        Returns:
            List of node IDs in topological order

        Raises:
            ValueError: If graph contains a cycle
        """
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Build adjacency list and in-degree count
        in_degree: Dict[str, int] = {node["id"]: 0 for node in nodes}
        adjacency: Dict[str, List[str]] = {node["id"]: [] for node in nodes}

        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            if from_id in adjacency and to_id in in_degree:
                adjacency[from_id].append(to_id)
                in_degree[to_id] += 1

        # Queue of nodes with no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(nodes):
            raise ValueError("Graph contains a cycle")

        return result

    def render_mermaid(self, graph: Dict[str, Any], include_status: bool = True) -> str:
        """
        Render task graph as Mermaid diagram.

        Args:
            graph: Task graph dictionary
            include_status: If True, include status colors

        Returns:
            Mermaid diagram string
        """
        # Role to emoji mapping
        role_emoji = {
            "eye": "\U0001F441\uFE0F",      # 👁️
            "ear": "\U0001F442",             # 👂
            "nose": "\U0001F443",            # 👃
            "tongue": "\U0001F445",          # 👅
            "body": "\u2694\uFE0F",          # ⚔️
            "mind": "\U0001F9E0",            # 🧠
        }

        lines = ["graph TD"]
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Track nodes by status for styling
        status_nodes: Dict[str, List[str]] = {
            "done": [],
            "running": [],
            "failed": [],
        }

        # Render nodes
        for node in nodes:
            node_id = node["id"]
            role = node.get("role", "unknown")
            title = node.get("title", node_id)
            emoji = role_emoji.get(role, "")

            # Format: node_id[emoji: title]
            label = f"{emoji}: {title}" if emoji else title
            lines.append(f"    {node_id}[{label}]")

            # Track status for styling
            status = node.get("status", "pending")
            if status in status_nodes:
                status_nodes[status].append(node_id)

        # Add blank line before edges
        if edges:
            lines.append("")

        # Render edges
        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            condition = edge.get("condition", "on_success")

            if condition == "on_success":
                lines.append(f"    {from_id} --> {to_id}")
            elif condition == "on_failure":
                lines.append(f"    {from_id} -->|on_failure| {to_id}")
            elif condition == "always":
                lines.append(f"    {from_id} -->|always| {to_id}")
            else:
                lines.append(f"    {from_id} -->|{condition}| {to_id}")

        # Add status styling if requested
        if include_status:
            lines.append("")
            lines.append("    classDef done fill:#90EE90")
            lines.append("    classDef running fill:#87CEEB")
            lines.append("    classDef failed fill:#FFB6C1")

            # Apply classes to nodes
            for status, node_ids in status_nodes.items():
                if node_ids:
                    lines.append(f"    class {','.join(node_ids)} {status}")

        return "\n".join(lines)
