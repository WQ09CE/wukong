"""
Wukong ArtifactManager - Output artifact archival

Manages archival and retrieval of subagent outputs.
Artifacts are stored in a structured directory hierarchy.
"""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid


class ArtifactManager:
    """
    Manages output artifacts from subagent executions.

    Artifacts are stored in a hierarchical structure:
        artifacts_dir/
        ├── {graph_id}/
        │   ├── {node_id}/
        │   │   ├── output.json       # Structured output
        │   │   ├── summary.md        # Human-readable summary
        │   │   └── files/            # Additional output files
        │   └── manifest.json         # Graph-level manifest
        └── index.json                # Global index

    Example:
        manager = ArtifactManager(Path("~/.wukong/artifacts"))
        artifact_path = manager.archive_output(
            graph_id="tg_abc123",
            node_id="eye_explore",
            output={"summary": "Found 3 files", "files": ["a.py", "b.py"]}
        )
        artifact = manager.get_artifact(artifact_path)
    """

    def __init__(self, artifacts_dir: Path):
        """
        Initialize the ArtifactManager.

        Args:
            artifacts_dir: Base directory for artifact storage
        """
        self.artifacts_dir = Path(artifacts_dir).expanduser()

        # Ensure base directory exists
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def _get_graph_dir(self, graph_id: str) -> Path:
        """Get the directory for a specific graph."""
        return self.artifacts_dir / graph_id

    def _get_node_dir(self, graph_id: str, node_id: str) -> Path:
        """Get the directory for a specific node within a graph."""
        return self._get_graph_dir(graph_id) / node_id

    def archive_output(
        self,
        graph_id: str,
        node_id: str,
        output: Dict[str, Any],
        summary: Optional[str] = None,
        files: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Archive the output from a node execution.

        Args:
            graph_id: ID of the task graph
            node_id: ID of the node that produced the output
            output: Structured output dictionary
            summary: Optional human-readable summary (Markdown)
            files: Optional additional files to archive {filename: content}

        Returns:
            Path to the archived output (relative to artifacts_dir)
        """
        # Create node directory
        node_dir = self._get_node_dir(graph_id, node_id)
        node_dir.mkdir(parents=True, exist_ok=True)

        # Add metadata to output
        archived_output = {
            "graph_id": graph_id,
            "node_id": node_id,
            "archived_at": self._get_timestamp(),
            "output": output,
        }

        # Write structured output
        output_file = node_dir / "output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(archived_output, f, indent=2, ensure_ascii=False)

        # Write summary if provided
        if summary:
            summary_file = node_dir / "summary.md"
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary)

        # Write additional files if provided
        if files:
            files_dir = node_dir / "files"
            files_dir.mkdir(exist_ok=True)
            for filename, content in files.items():
                file_path = files_dir / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

        # Update graph manifest
        self._update_manifest(graph_id, node_id)

        # Update global index
        self._update_index(graph_id)

        # Return relative path
        return f"{graph_id}/{node_id}/output.json"

    def _update_manifest(self, graph_id: str, node_id: str) -> None:
        """Update the graph-level manifest with new node artifact."""
        graph_dir = self._get_graph_dir(graph_id)
        manifest_file = graph_dir / "manifest.json"

        # Load existing manifest or create new
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        else:
            manifest = {
                "graph_id": graph_id,
                "created_at": self._get_timestamp(),
                "nodes": {},
            }

        # Add/update node entry
        manifest["nodes"][node_id] = {
            "archived_at": self._get_timestamp(),
            "path": f"{node_id}/output.json",
        }
        manifest["updated_at"] = self._get_timestamp()

        # Save manifest
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def _update_index(self, graph_id: str) -> None:
        """Update the global index with graph entry."""
        index_file = self.artifacts_dir / "index.json"

        # Load existing index or create new
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {
                "graphs": {},
                "created_at": self._get_timestamp(),
            }

        # Add/update graph entry
        index["graphs"][graph_id] = {
            "updated_at": self._get_timestamp(),
            "path": f"{graph_id}/manifest.json",
        }
        index["updated_at"] = self._get_timestamp()

        # Save index
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def get_artifact(self, artifact_path: str) -> Dict[str, Any]:
        """
        Retrieve an artifact by its path.

        Args:
            artifact_path: Relative path to the artifact (from archive_output)

        Returns:
            Artifact content as dictionary

        Raises:
            FileNotFoundError: If artifact doesn't exist
        """
        full_path = self.artifacts_dir / artifact_path

        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {artifact_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_node_output(
        self,
        graph_id: str,
        node_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the output from a specific node.

        Args:
            graph_id: ID of the task graph
            node_id: ID of the node

        Returns:
            Output dictionary, or None if not found
        """
        try:
            artifact = self.get_artifact(f"{graph_id}/{node_id}/output.json")
            return artifact.get("output", {})
        except FileNotFoundError:
            return None

    def get_node_summary(
        self,
        graph_id: str,
        node_id: str,
    ) -> Optional[str]:
        """
        Get the summary from a specific node.

        Args:
            graph_id: ID of the task graph
            node_id: ID of the node

        Returns:
            Summary string, or None if not found
        """
        summary_file = self._get_node_dir(graph_id, node_id) / "summary.md"

        if not summary_file.exists():
            return None

        with open(summary_file, "r", encoding="utf-8") as f:
            return f.read()

    def list_artifacts(self, graph_id: str) -> List[str]:
        """
        List all artifact paths for a specific graph.

        Args:
            graph_id: ID of the task graph

        Returns:
            List of artifact paths (relative to artifacts_dir)
        """
        graph_dir = self._get_graph_dir(graph_id)

        if not graph_dir.exists():
            return []

        artifacts = []

        for node_dir in graph_dir.iterdir():
            if node_dir.is_dir() and node_dir.name != "files":
                output_file = node_dir / "output.json"
                if output_file.exists():
                    artifacts.append(f"{graph_id}/{node_dir.name}/output.json")

        return artifacts

    def list_graphs(self) -> List[str]:
        """
        List all graph IDs with archived artifacts.

        Returns:
            List of graph IDs
        """
        graphs = []

        for item in self.artifacts_dir.iterdir():
            if item.is_dir() and item.name.startswith("tg_"):
                graphs.append(item.name)

        return graphs

    def get_manifest(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the manifest for a specific graph.

        Args:
            graph_id: ID of the task graph

        Returns:
            Manifest dictionary, or None if not found
        """
        manifest_file = self._get_graph_dir(graph_id) / "manifest.json"

        if not manifest_file.exists():
            return None

        with open(manifest_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete_graph_artifacts(self, graph_id: str) -> bool:
        """
        Delete all artifacts for a specific graph.

        Args:
            graph_id: ID of the task graph

        Returns:
            True if deleted, False if not found
        """
        graph_dir = self._get_graph_dir(graph_id)

        if not graph_dir.exists():
            return False

        # Remove directory and all contents
        shutil.rmtree(graph_dir)

        # Update index
        index_file = self.artifacts_dir / "index.json"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)

            if graph_id in index.get("graphs", {}):
                del index["graphs"][graph_id]
                index["updated_at"] = self._get_timestamp()

                with open(index_file, "w", encoding="utf-8") as f:
                    json.dump(index, f, indent=2, ensure_ascii=False)

        return True

    def cleanup_old_artifacts(
        self,
        max_age_days: int = 30,
        max_graphs: Optional[int] = None,
    ) -> List[str]:
        """
        Clean up old artifacts based on age or count.

        Args:
            max_age_days: Maximum age in days (delete older)
            max_graphs: Maximum number of graphs to keep (delete oldest)

        Returns:
            List of deleted graph IDs
        """
        deleted = []
        graphs = self.list_graphs()

        # Get graph info with timestamps
        graph_info = []
        for graph_id in graphs:
            manifest = self.get_manifest(graph_id)
            if manifest:
                created = manifest.get("created_at", "")
                graph_info.append((graph_id, created))

        # Sort by creation time (oldest first)
        graph_info.sort(key=lambda x: x[1])

        # Delete by age
        now = datetime.now(timezone.utc)
        for graph_id, created in graph_info:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                age = (now - created_dt).days
                if age > max_age_days:
                    if self.delete_graph_artifacts(graph_id):
                        deleted.append(graph_id)
            except (ValueError, TypeError):
                continue

        # Delete by count (if still over limit)
        if max_graphs and len(graphs) - len(deleted) > max_graphs:
            remaining = [g for g, _ in graph_info if g not in deleted]
            to_delete = len(remaining) - max_graphs

            for graph_id in remaining[:to_delete]:
                if self.delete_graph_artifacts(graph_id):
                    deleted.append(graph_id)

        return deleted
