"""
Wukong AnchorManager - Anchor management for cross-session knowledge persistence

Anchors are persistent pieces of knowledge that survive across sessions:
- Architecture decisions (ADR)
- Constraints
- Interface definitions
- Important lessons learned

Anchors are stored in a structured format with indexing for efficient retrieval.
"""

import json
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set


# Anchor types
ANCHOR_TYPES = {"decision", "constraint", "interface", "lesson"}

# Evidence levels
EVIDENCE_LEVELS = {"L0", "L1", "L2", "L3"}


class AnchorManager:
    """
    Manages anchors for cross-session knowledge persistence.

    Anchors are stored in:
        anchors_dir/
        ├── anchors.json         # Main anchor index
        ├── candidates.json      # Candidate anchors pending promotion
        └── {project}/           # Project-specific anchors
            └── anchors.json

    Example:
        manager = AnchorManager(Path("~/.wukong/anchors"))
        candidate_id = manager.add_candidate({
            "type": "decision",
            "title": "Use JWT for authentication",
            "content": "JWT was chosen for stateless auth...",
            "keywords": ["auth", "jwt", "security"]
        })
        anchor_id = manager.promote_anchor(candidate_id)
        results = manager.search_anchors(["auth", "security"])
    """

    def __init__(self, anchors_dir: Path):
        """
        Initialize the AnchorManager.

        Args:
            anchors_dir: Base directory for anchor storage
        """
        self.anchors_dir = Path(anchors_dir).expanduser()

        # Ensure directories exist
        self.anchors_dir.mkdir(parents=True, exist_ok=True)

        # Initialize index files if they don't exist
        self._init_index_files()

    def _init_index_files(self) -> None:
        """Initialize index files if they don't exist."""
        anchors_file = self.anchors_dir / "anchors.json"
        candidates_file = self.anchors_dir / "candidates.json"

        if not anchors_file.exists():
            self._write_json(anchors_file, {
                "anchors": {},
                "created_at": self._get_timestamp(),
                "updated_at": self._get_timestamp(),
            })

        if not candidates_file.exists():
            self._write_json(candidates_file, {
                "candidates": {},
                "created_at": self._get_timestamp(),
                "updated_at": self._get_timestamp(),
            })

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def _generate_anchor_id(self) -> str:
        """Generate a unique anchor ID matching pattern ^anc_[a-z0-9]+$."""
        return f"anc_{uuid.uuid4().hex[:12]}"

    def _generate_candidate_id(self) -> str:
        """Generate a unique candidate ID matching pattern ^cand_[a-z0-9]+$."""
        return f"cand_{uuid.uuid4().hex[:12]}"

    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file with error handling."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write JSON file atomically."""
        temp_path = file_path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)

    def add_candidate(
        self,
        anchor: Dict[str, Any],
        source: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Add a candidate anchor pending promotion.

        Args:
            anchor: Anchor data with required fields:
                - type: decision|constraint|interface|lesson
                - title: Short descriptive title
                - content: Full anchor content
                - keywords: List of keywords for search
            source: Optional source information:
                - graph_id: Task graph that produced this
                - node_id: Node that produced this

        Returns:
            The generated candidate ID

        Raises:
            ValueError: If anchor data is invalid
        """
        # Validate required fields
        if "type" not in anchor:
            raise ValueError("Anchor must have a 'type' field")
        if anchor["type"] not in ANCHOR_TYPES:
            raise ValueError(
                f"Invalid anchor type: {anchor['type']}. "
                f"Must be one of: {sorted(ANCHOR_TYPES)}"
            )
        if "title" not in anchor or not anchor["title"]:
            raise ValueError("Anchor must have a non-empty 'title' field")
        if "content" not in anchor or not anchor["content"]:
            raise ValueError("Anchor must have a non-empty 'content' field")

        # Generate candidate ID
        candidate_id = self._generate_candidate_id()

        # Build candidate record
        candidate = {
            "id": candidate_id,
            "type": anchor["type"],
            "title": anchor["title"],
            "content": anchor["content"],
            "keywords": anchor.get("keywords", []),
            "created_at": self._get_timestamp(),
            "evidence_level": anchor.get("evidence_level", "L1"),
        }

        # Add source if provided
        if source:
            candidate["source"] = source

        # Load and update candidates file
        candidates_file = self.anchors_dir / "candidates.json"
        data = self._read_json(candidates_file)
        if "candidates" not in data:
            data["candidates"] = {}

        data["candidates"][candidate_id] = candidate
        data["updated_at"] = self._get_timestamp()

        self._write_json(candidates_file, data)

        return candidate_id

    def promote_anchor(
        self,
        candidate_id: str,
        project: Optional[str] = None,
    ) -> str:
        """
        Promote a candidate to a full anchor.

        Args:
            candidate_id: ID of the candidate to promote
            project: Optional project name for project-specific anchors

        Returns:
            The generated anchor ID

        Raises:
            ValueError: If candidate not found
        """
        # Load candidates
        candidates_file = self.anchors_dir / "candidates.json"
        candidates_data = self._read_json(candidates_file)
        candidates = candidates_data.get("candidates", {})

        if candidate_id not in candidates:
            raise ValueError(f"Candidate not found: {candidate_id}")

        candidate = candidates[candidate_id]

        # Generate anchor ID
        anchor_id = self._generate_anchor_id()

        # Build anchor record
        anchor = {
            "id": anchor_id,
            "type": candidate["type"],
            "title": candidate["title"],
            "content": candidate["content"],
            "keywords": candidate.get("keywords", []),
            "created_at": candidate.get("created_at", self._get_timestamp()),
            "promoted_at": self._get_timestamp(),
            "evidence_level": candidate.get("evidence_level", "L1"),
        }

        # Copy source if present
        if "source" in candidate:
            anchor["source"] = candidate["source"]

        # Determine target file
        if project:
            project_dir = self.anchors_dir / project
            project_dir.mkdir(parents=True, exist_ok=True)
            anchors_file = project_dir / "anchors.json"
        else:
            anchors_file = self.anchors_dir / "anchors.json"

        # Load and update anchors file
        anchors_data = self._read_json(anchors_file)
        if "anchors" not in anchors_data:
            anchors_data["anchors"] = {}

        anchors_data["anchors"][anchor_id] = anchor
        anchors_data["updated_at"] = self._get_timestamp()

        self._write_json(anchors_file, anchors_data)

        # Remove from candidates
        del candidates[candidate_id]
        candidates_data["candidates"] = candidates
        candidates_data["updated_at"] = self._get_timestamp()
        self._write_json(candidates_file, candidates_data)

        return anchor_id

    def search_anchors(
        self,
        keywords: List[str],
        project: Optional[str] = None,
        anchor_type: Optional[str] = None,
        include_global: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search anchors by keywords.

        Args:
            keywords: List of keywords to search for (OR logic)
            project: Optional project to search in
            anchor_type: Optional filter by anchor type
            include_global: Whether to include global anchors

        Returns:
            List of matching anchors sorted by relevance
        """
        results: List[Dict[str, Any]] = []
        keywords_lower = [kw.lower() for kw in keywords]

        # Collect anchors to search
        anchor_files: List[Path] = []

        if include_global:
            global_file = self.anchors_dir / "anchors.json"
            if global_file.exists():
                anchor_files.append(global_file)

        if project:
            project_file = self.anchors_dir / project / "anchors.json"
            if project_file.exists():
                anchor_files.append(project_file)

        # Search each file
        for anchor_file in anchor_files:
            data = self._read_json(anchor_file)
            anchors = data.get("anchors", {})

            for anchor_id, anchor in anchors.items():
                # Filter by type if specified
                if anchor_type and anchor.get("type") != anchor_type:
                    continue

                # Calculate relevance score
                score = self._calculate_relevance(anchor, keywords_lower)
                if score > 0:
                    anchor_copy = anchor.copy()
                    anchor_copy["_relevance_score"] = score
                    results.append(anchor_copy)

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)

        # Remove internal score field
        for result in results:
            result.pop("_relevance_score", None)

        return results

    def _calculate_relevance(
        self,
        anchor: Dict[str, Any],
        keywords_lower: List[str],
    ) -> int:
        """Calculate relevance score for an anchor based on keywords."""
        score = 0

        # Check keywords field (highest weight)
        anchor_keywords = [kw.lower() for kw in anchor.get("keywords", [])]
        for kw in keywords_lower:
            if kw in anchor_keywords:
                score += 10

        # Check title (medium weight)
        title_lower = anchor.get("title", "").lower()
        for kw in keywords_lower:
            if kw in title_lower:
                score += 5

        # Check content (lower weight)
        content_lower = anchor.get("content", "").lower()
        for kw in keywords_lower:
            if kw in content_lower:
                score += 1

        return score

    def get_relevant_anchors(
        self,
        task_description: str,
        project: Optional[str] = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get anchors relevant to a task description.

        Extracts keywords from the task description and searches anchors.

        Args:
            task_description: Natural language task description
            project: Optional project context
            max_results: Maximum number of results to return

        Returns:
            List of relevant anchors
        """
        # Extract keywords from task description
        keywords = self._extract_keywords(task_description)

        if not keywords:
            return []

        # Search anchors
        results = self.search_anchors(
            keywords,
            project=project,
            include_global=True,
        )

        return results[:max_results]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text."""
        # Common stop words to filter out
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "to", "of", "in", "for", "on", "with", "at",
            "by", "from", "as", "into", "through", "during", "before",
            "after", "above", "below", "between", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "each", "few", "more", "most", "other",
            "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "just", "and", "but", "if", "or",
            "because", "until", "while", "this", "that", "these", "those",
            # Chinese stop words
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这",
        }

        # Tokenize: split on non-alphanumeric characters
        words = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())

        # Filter stop words and short words
        keywords = [
            word for word in words
            if word not in stop_words and len(word) > 1
        ]

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:10]  # Limit to 10 keywords

    def export_anchors_md(
        self,
        project: Optional[str] = None,
        include_global: bool = True,
    ) -> str:
        """
        Export anchors to Markdown format.

        Args:
            project: Optional project to export
            include_global: Whether to include global anchors

        Returns:
            Markdown formatted string
        """
        lines = ["# Anchors\n"]
        lines.append(f"_Exported at: {self._get_timestamp()}_\n")

        # Collect anchors
        all_anchors: Dict[str, List[Dict[str, Any]]] = {
            "decision": [],
            "constraint": [],
            "interface": [],
            "lesson": [],
        }

        # Load global anchors
        if include_global:
            global_file = self.anchors_dir / "anchors.json"
            if global_file.exists():
                data = self._read_json(global_file)
                for anchor in data.get("anchors", {}).values():
                    anchor_type = anchor.get("type", "lesson")
                    all_anchors[anchor_type].append(anchor)

        # Load project anchors
        if project:
            project_file = self.anchors_dir / project / "anchors.json"
            if project_file.exists():
                data = self._read_json(project_file)
                for anchor in data.get("anchors", {}).values():
                    anchor_type = anchor.get("type", "lesson")
                    all_anchors[anchor_type].append(anchor)

        # Format each type
        type_titles = {
            "decision": "Architecture Decisions",
            "constraint": "Constraints",
            "interface": "Interface Definitions",
            "lesson": "Lessons Learned",
        }

        for anchor_type, title in type_titles.items():
            anchors = all_anchors[anchor_type]
            if not anchors:
                continue

            lines.append(f"\n## {title}\n")

            for anchor in anchors:
                lines.append(f"### {anchor.get('title', 'Untitled')}\n")
                lines.append(f"**ID**: `{anchor.get('id', 'N/A')}`\n")
                lines.append(f"**Evidence Level**: {anchor.get('evidence_level', 'L1')}\n")

                keywords = anchor.get("keywords", [])
                if keywords:
                    lines.append(f"**Keywords**: {', '.join(keywords)}\n")

                lines.append(f"\n{anchor.get('content', '')}\n")

                if "source" in anchor:
                    source = anchor["source"]
                    lines.append(f"\n_Source: {source.get('graph_id', 'N/A')} / {source.get('node_id', 'N/A')}_\n")

                lines.append("---\n")

        return "\n".join(lines)

    def get_anchor(self, anchor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific anchor by ID.

        Args:
            anchor_id: The anchor ID

        Returns:
            Anchor dict or None if not found
        """
        # Search in global anchors
        global_file = self.anchors_dir / "anchors.json"
        if global_file.exists():
            data = self._read_json(global_file)
            if anchor_id in data.get("anchors", {}):
                return data["anchors"][anchor_id]

        # Search in project directories
        for item in self.anchors_dir.iterdir():
            if item.is_dir():
                project_file = item / "anchors.json"
                if project_file.exists():
                    data = self._read_json(project_file)
                    if anchor_id in data.get("anchors", {}):
                        return data["anchors"][anchor_id]

        return None

    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific candidate by ID.

        Args:
            candidate_id: The candidate ID

        Returns:
            Candidate dict or None if not found
        """
        candidates_file = self.anchors_dir / "candidates.json"
        if candidates_file.exists():
            data = self._read_json(candidates_file)
            return data.get("candidates", {}).get(candidate_id)
        return None

    def list_candidates(self) -> List[Dict[str, Any]]:
        """
        List all pending candidates.

        Returns:
            List of candidate dictionaries
        """
        candidates_file = self.anchors_dir / "candidates.json"
        if candidates_file.exists():
            data = self._read_json(candidates_file)
            return list(data.get("candidates", {}).values())
        return []

    def delete_candidate(self, candidate_id: str) -> bool:
        """
        Delete a candidate anchor.

        Args:
            candidate_id: The candidate ID to delete

        Returns:
            True if deleted, False if not found
        """
        candidates_file = self.anchors_dir / "candidates.json"
        if not candidates_file.exists():
            return False

        data = self._read_json(candidates_file)
        candidates = data.get("candidates", {})

        if candidate_id not in candidates:
            return False

        del candidates[candidate_id]
        data["candidates"] = candidates
        data["updated_at"] = self._get_timestamp()

        self._write_json(candidates_file, data)
        return True

    def delete_anchor(
        self,
        anchor_id: str,
        project: Optional[str] = None,
    ) -> bool:
        """
        Delete an anchor.

        Args:
            anchor_id: The anchor ID to delete
            project: Optional project name

        Returns:
            True if deleted, False if not found
        """
        # Determine file to search
        if project:
            anchors_file = self.anchors_dir / project / "anchors.json"
        else:
            anchors_file = self.anchors_dir / "anchors.json"

        if not anchors_file.exists():
            return False

        data = self._read_json(anchors_file)
        anchors = data.get("anchors", {})

        if anchor_id not in anchors:
            return False

        del anchors[anchor_id]
        data["anchors"] = anchors
        data["updated_at"] = self._get_timestamp()

        self._write_json(anchors_file, data)
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about anchors.

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_anchors": 0,
            "total_candidates": 0,
            "by_type": {t: 0 for t in ANCHOR_TYPES},
            "by_level": {l: 0 for l in EVIDENCE_LEVELS},
            "projects": [],
        }

        # Count global anchors
        global_file = self.anchors_dir / "anchors.json"
        if global_file.exists():
            data = self._read_json(global_file)
            for anchor in data.get("anchors", {}).values():
                stats["total_anchors"] += 1
                anchor_type = anchor.get("type", "lesson")
                if anchor_type in stats["by_type"]:
                    stats["by_type"][anchor_type] += 1
                level = anchor.get("evidence_level", "L1")
                if level in stats["by_level"]:
                    stats["by_level"][level] += 1

        # Count candidates
        candidates_file = self.anchors_dir / "candidates.json"
        if candidates_file.exists():
            data = self._read_json(candidates_file)
            stats["total_candidates"] = len(data.get("candidates", {}))

        # Count project anchors
        for item in self.anchors_dir.iterdir():
            if item.is_dir() and (item / "anchors.json").exists():
                project_name = item.name
                stats["projects"].append(project_name)

                data = self._read_json(item / "anchors.json")
                for anchor in data.get("anchors", {}).values():
                    stats["total_anchors"] += 1
                    anchor_type = anchor.get("type", "lesson")
                    if anchor_type in stats["by_type"]:
                        stats["by_type"][anchor_type] += 1
                    level = anchor.get("evidence_level", "L1")
                    if level in stats["by_level"]:
                        stats["by_level"][level] += 1

        return stats
