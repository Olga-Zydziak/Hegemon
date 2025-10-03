"""
HEGEMON HITL Custom Exceptions - Phase 2.1.

Hierarchia wyjątków dla Human-in-the-Loop functionality.

Exception Hierarchy:
    HITLError (base)
    ├── CheckpointError
    ├── FeedbackValidationError
    ├── MaxRevisionsExceededError
    └── StateCorruptionError

Complexity: O(1) dla wszystkich operacji exception
"""

from __future__ import annotations


# ============================================================================
# Base Exception
# ============================================================================

class HITLError(Exception):
    """
    Base exception dla wszystkich HITL errors.
    
    Wszystkie custom exceptions w module HITL dziedziczą po tej klasie
    dla łatwego catch-all handling.
    """
    pass


# ============================================================================
# Checkpoint Exceptions
# ============================================================================

class CheckpointError(HITLError):
    """
    Raised when checkpoint operation fails.
    
    Examples:
        - Checkpoint node execution error
        - Invalid checkpoint state
        - Checkpoint timeout
    """
    pass


# ============================================================================
# Feedback Exceptions
# ============================================================================

class FeedbackValidationError(HITLError):
    """
    Raised when feedback validation fails.
    
    Examples:
        - Missing required guidance for revision
        - Invalid feedback decision
        - Dangerous patterns detected
    """
    pass


class MaxRevisionsExceededError(HITLError):
    """
    Raised when revision limit exceeded for checkpoint.
    
    Prevents infinite revision loops. Default limit: 3 revisions per checkpoint.
    
    Attributes:
        checkpoint: Checkpoint identifier
        current_count: Current revision count
        max_allowed: Maximum revisions allowed
    """
    
    def __init__(
        self,
        checkpoint: str,
        current_count: int,
        max_allowed: int = 3
    ) -> None:
        self.checkpoint = checkpoint
        self.current_count = current_count
        self.max_allowed = max_allowed
        
        message = (
            f"Maximum revisions exceeded for checkpoint '{checkpoint}'. "
            f"Current: {current_count}, Max: {max_allowed}. "
            f"Please approve or reject to proceed."
        )
        super().__init__(message)


# ============================================================================
# State Management Exceptions
# ============================================================================

class StateCorruptionError(HITLError):
    """
    Raised when state corruption detected.
    
    Examples:
        - Missing checkpoint snapshot
        - State checksum mismatch
        - Corrupted serialization
    
    This is a CRITICAL error indicating data integrity issue.
    System should attempt recovery from last valid checkpoint.
    """
    pass