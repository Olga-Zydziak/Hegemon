"""
File Manager for Debate Outputs.

Handles automatic saving of debate results, checkpoints, and feedback logs.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class FileManager:
    """Manages file operations for debate outputs.
    
    Automatically saves debate results to output directory with:
    - Timestamped filenames
    - Organized folder structure
    - JSON formatting
    - Optional compression
    
    Complexity: O(n) for file operations where n = data size
    """
    
    def __init__(self, base_output_dir: str | Path = "output/streamlit"):
        """Initialize file manager.
        
        Args:
            base_output_dir: Base directory for outputs
        """
        self.base_dir = Path(base_output_dir)
        self.debates_dir = self.base_dir / "debates"
        self.checkpoints_dir = self.base_dir / "checkpoints"
        self.feedback_dir = self.base_dir / "feedback"
        
        # Create directories
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create output directories if they don't exist.
        
        Complexity: O(1)
        """
        self.debates_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
    
    def save_debate_result(
        self,
        final_state: dict[str, Any],
        mission: str,
        mode: str,
    ) -> Path:
        """Save complete debate result to file.
        
        Args:
            final_state: Final debate state
            mission: Mission description
            mode: Intervention mode
            
        Returns:
            Path to saved file
            
        Complexity: O(n) where n = size of final_state
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debate_{timestamp}.json"
        filepath = self.debates_dir / filename
        
        # Prepare data with metadata
        output_data = {
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "mission_preview": mission[:200],
                "intervention_mode": mode,
                "filename": filename,
            },
            "debate_state": final_state,
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    def save_checkpoint_snapshot(
        self,
        checkpoint_data: dict[str, Any],
        cycle: int,
        checkpoint_type: str,
    ) -> Path:
        """Save checkpoint snapshot (optional detailed logging).
        
        Args:
            checkpoint_data: Checkpoint data
            cycle: Cycle number
            checkpoint_type: Type of checkpoint
            
        Returns:
            Path to saved file
            
        Complexity: O(n) where n = size of checkpoint_data
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_cycle{cycle}_{checkpoint_type}_{timestamp}.json"
        filepath = self.checkpoints_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    def save_feedback_log(
        self,
        feedback_history: list[dict[str, Any]],
    ) -> Path:
        """Save complete feedback history.
        
        Args:
            feedback_history: All collected feedback
            
        Returns:
            Path to saved file
            
        Complexity: O(n) where n = len(feedback_history)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feedback_log_{timestamp}.json"
        filepath = self.feedback_dir / filename
        
        output_data = {
            "saved_at": datetime.now().isoformat(),
            "total_feedbacks": len(feedback_history),
            "feedbacks": feedback_history,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    def list_saved_debates(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recently saved debates.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of debate metadata
            
        Complexity: O(n log n) where n = number of files
        """
        debate_files = sorted(
            self.debates_dir.glob("debate_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]
        
        results = []
        for filepath in debate_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                results.append({
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "size_kb": filepath.stat().st_size / 1024,
                    "created": datetime.fromtimestamp(
                        filepath.stat().st_ctime
                    ).isoformat(),
                    "mission_preview": data.get("metadata", {}).get(
                        "mission_preview", "N/A"
                    ),
                })
            except Exception:
                continue
        
        return results
    
    def load_debate(self, filepath: str | Path) -> dict[str, Any]:
        """Load saved debate from file.
        
        Args:
            filepath: Path to debate file
            
        Returns:
            Debate data
            
        Complexity: O(n) where n = file size
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def delete_debate(self, filepath: str | Path) -> bool:
        """Delete saved debate file.
        
        Args:
            filepath: Path to debate file
            
        Returns:
            True if deleted successfully
            
        Complexity: O(1)
        """
        try:
            Path(filepath).unlink()
            return True
        except Exception:
            return False
    
    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Storage stats dict
            
        Complexity: O(n) where n = number of files
        """
        debate_files = list(self.debates_dir.glob("*.json"))
        checkpoint_files = list(self.checkpoints_dir.glob("*.json"))
        feedback_files = list(self.feedback_dir.glob("*.json"))
        
        total_size = sum(
            f.stat().st_size
            for f in debate_files + checkpoint_files + feedback_files
        )
        
        return {
            "total_debates": len(debate_files),
            "total_checkpoints": len(checkpoint_files),
            "total_feedback_logs": len(feedback_files),
            "total_size_mb": total_size / (1024 * 1024),
            "debates_dir": str(self.debates_dir.absolute()),
        }
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """Delete files older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of files deleted
            
        Complexity: O(n) where n = number of files
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0
        
        for directory in [self.debates_dir, self.checkpoints_dir, self.feedback_dir]:
            for filepath in directory.glob("*.json"):
                if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff:
                    try:
                        filepath.unlink()
                        deleted += 1
                    except Exception:
                        continue
        
        return deleted


def create_file_manager(output_dir: str | Path = "output/streamlit") -> FileManager:
    """Factory function for file manager.
    
    Args:
        output_dir: Output directory path
        
    Returns:
        FileManager instance
        
    Complexity: O(1)
    """
    return FileManager(output_dir)
