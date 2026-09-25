"""
Undo/Redo Manager

Provides undo/redo functionality for operator actions.

Features:
- Command pattern implementation
- Undo/Redo stack management
- Action grouping (composite commands)
- History limit
- Clear history

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)


class Command(ABC):
    """
    Abstract base class for undoable commands.
    
    All undoable actions must implement this interface.
    """
    
    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the command.
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """
        Undo the command.
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def redo(self) -> bool:
        """
        Redo the command (default: call execute).
        
        Returns:
            True if successful
        """
        return self.execute()
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Get human-readable description of command.
        
        Returns:
            Command description
        """
        pass


class CompositeCommand(Command):
    """
    Composite command that groups multiple commands together.
    
    Useful for transactions (all-or-nothing operations).
    """
    
    def __init__(self, description: str):
        """
        Initialize composite command.
        
        Args:
            description: Description of the grouped operation
        """
        self._commands: List[Command] = []
        self._description = description
    
    def add_command(self, command: Command):
        """Add command to group."""
        self._commands.append(command)
    
    def execute(self) -> bool:
        """Execute all commands."""
        for command in self._commands:
            if not command.execute():
                # Rollback on failure
                self._rollback_executed()
                return False
        return True
    
    def undo(self) -> bool:
        """Undo all commands in reverse order."""
        # Undo in reverse order
        for command in reversed(self._commands):
            if not command.undo():
                logger.error(f"Failed to undo command in composite: {command.get_description()}")
                return False
        return True
    
    def redo(self) -> bool:
        """Redo all commands."""
        return self.execute()
    
    def _rollback_executed(self):
        """Rollback any commands that were executed."""
        logger.warning("Rolling back composite command due to failure")
        for i in range(len(self._commands) - 1, -1, -1):
            try:
                self._commands[i].undo()
            except Exception as e:
                logger.error(f"Error rolling back command: {e}")
    
    def get_description(self) -> str:
        """Get description."""
        return self._description


class UndoManager(QObject):
    """
    Manages undo/redo stacks and command execution.
    
    Features:
    - Undo/Redo operations
    - History limit
    - Clear history
    - State change notifications
    """
    
    # Signals
    can_undo_changed = pyqtSignal(bool)
    can_redo_changed = pyqtSignal(bool)
    history_changed = pyqtSignal()
    command_executed = pyqtSignal(str)  # command description
    command_undone = pyqtSignal(str)
    command_redone = pyqtSignal(str)
    
    def __init__(self, history_limit: int = 100):
        """
        Initialize undo manager.
        
        Args:
            history_limit: Maximum number of commands to keep in history
        """
        super().__init__()
        
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._history_limit = history_limit
        
        logger.info(f"UndoManager initialized (limit: {history_limit})")
    
    def execute(self, command: Command) -> bool:
        """
        Execute a command and add to undo stack.
        
        Args:
            command: Command to execute
        
        Returns:
            True if executed successfully
        """
        try:
            # Execute command
            success = command.execute()
            
            if success:
                # Add to undo stack
                self._undo_stack.append(command)
                
                # Clear redo stack (new action invalidates redo)
                self._redo_stack.clear()
                
                # Enforce history limit
                if len(self._undo_stack) > self._history_limit:
                    removed = self._undo_stack.pop(0)
                    logger.debug(f"Removed old command from history: {removed.get_description()}")
                
                logger.info(f"✅ Executed: {command.get_description()}")
                self.command_executed.emit(command.get_description())
                
                # Notify state changes
                self._emit_state_changes()
                
                return True
            else:
                logger.error(f"❌ Failed to execute: {command.get_description()}")
                return False
                
        except Exception as e:
            logger.error(f"Exception executing command: {e}")
            return False
    
    def undo(self) -> bool:
        """
        Undo last command.
        
        Returns:
            True if undone successfully
        """
        if not self.can_undo():
            logger.warning("Cannot undo: no commands in undo stack")
            return False
        
        try:
            # Pop from undo stack
            command = self._undo_stack.pop()
            
            # Undo it
            success = command.undo()
            
            if success:
                # Add to redo stack
                self._redo_stack.append(command)
                
                logger.info(f"↶ Undone: {command.get_description()}")
                self.command_undone.emit(command.get_description())
                
                # Notify state changes
                self._emit_state_changes()
                
                return True
            else:
                # Put it back if undo failed
                self._undo_stack.append(command)
                logger.error(f"Failed to undo: {command.get_description()}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during undo: {e}")
            return False
    
    def redo(self) -> bool:
        """
        Redo last undone command.
        
        Returns:
            True if redone successfully
        """
        if not self.can_redo():
            logger.warning("Cannot redo: no commands in redo stack")
            return False
        
        try:
            # Pop from redo stack
            command = self._redo_stack.pop()
            
            # Redo it
            success = command.redo()
            
            if success:
                # Add back to undo stack
                self._undo_stack.append(command)
                
                logger.info(f"↷ Redone: {command.get_description()}")
                self.command_redone.emit(command.get_description())
                
                # Notify state changes
                self._emit_state_changes()
                
                return True
            else:
                # Put it back if redo failed
                self._redo_stack.append(command)
                logger.error(f"Failed to redo: {command.get_description()}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during redo: {e}")
            return False
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of command that would be undone."""
        if self.can_undo():
            return self._undo_stack[-1].get_description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of command that would be redone."""
        if self.can_redo():
            return self._redo_stack[-1].get_description()
        return None
    
    def get_undo_history(self) -> List[str]:
        """Get list of undo command descriptions."""
        return [cmd.get_description() for cmd in self._undo_stack]
    
    def get_redo_history(self) -> List[str]:
        """Get list of redo command descriptions."""
        return [cmd.get_description() for cmd in self._redo_stack]
    
    def clear_history(self):
        """Clear all undo/redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.info("Cleared undo/redo history")
        self._emit_state_changes()
    
    def set_history_limit(self, limit: int):
        """
        Set history limit.
        
        Args:
            limit: New history limit
        """
        self._history_limit = limit
        
        # Trim if necessary
        if len(self._undo_stack) > limit:
            self._undo_stack = self._undo_stack[-limit:]
            logger.info(f"Trimmed history to {limit} commands")
    
    def _emit_state_changes(self):
        """Emit state change signals."""
        self.can_undo_changed.emit(self.can_undo())
        self.can_redo_changed.emit(self.can_redo())
        self.history_changed.emit()


# Example command implementations

class SetValueCommand(Command):
    """Example: Set a value with undo support."""
    
    def __init__(self, obj: object, attr: str, new_value: any, description: str = None):
        """
        Initialize command.
        
        Args:
            obj: Object to modify
            attr: Attribute name
            new_value: New value
            description: Optional description
        """
        self._obj = obj
        self._attr = attr
        self._new_value = new_value
        self._old_value = None
        self._description = description or f"Set {attr}"
    
    def execute(self) -> bool:
        """Execute: save old value and set new value."""
        try:
            self._old_value = getattr(self._obj, self._attr)
            setattr(self._obj, self._attr, self._new_value)
            return True
        except Exception as e:
            logger.error(f"Failed to set value: {e}")
            return False
    
    def undo(self) -> bool:
        """Undo: restore old value."""
        try:
            setattr(self._obj, self._attr, self._old_value)
            return True
        except Exception as e:
            logger.error(f"Failed to undo set value: {e}")
            return False
    
    def get_description(self) -> str:
        """Get description."""
        return f"{self._description}: {self._old_value} → {self._new_value}"


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== Undo Manager Test ===\n")
    
    # Create manager
    undo_manager = UndoManager(history_limit=10)
    
    # Test object
    class TestObject:
        def __init__(self):
            self.value = 0
    
    obj = TestObject()
    
    # Execute commands
    print(f"Initial value: {obj.value}")
    
    cmd1 = SetValueCommand(obj, 'value', 10, "Set to 10")
    undo_manager.execute(cmd1)
    print(f"After cmd1: {obj.value}")
    
    cmd2 = SetValueCommand(obj, 'value', 20, "Set to 20")
    undo_manager.execute(cmd2)
    print(f"After cmd2: {obj.value}")
    
    cmd3 = SetValueCommand(obj, 'value', 30, "Set to 30")
    undo_manager.execute(cmd3)
    print(f"After cmd3: {obj.value}")
    
    # Undo
    print("\n=== Undo ===")
    undo_manager.undo()
    print(f"After undo: {obj.value}")
    
    undo_manager.undo()
    print(f"After undo: {obj.value}")
    
    # Redo
    print("\n=== Redo ===")
    undo_manager.redo()
    print(f"After redo: {obj.value}")
    
    # History
    print("\n=== History ===")
    print(f"Undo stack: {undo_manager.get_undo_history()}")
    print(f"Redo stack: {undo_manager.get_redo_history()}")

