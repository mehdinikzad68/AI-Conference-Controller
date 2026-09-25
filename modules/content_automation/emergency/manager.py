"""
Emergency Manager - Crisis Scenario Management

Handles:
- Predefined emergency scenarios
- Automatic fallback content
- Network failure handling
- Speaker absence scenarios
"""

import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..sync.event_bus import get_event_bus, Event, EventType
from ..models import ContentType, Priority

logger = logging.getLogger(__name__)


class EmergencyType(Enum):
    """Emergency scenario types"""
    SPEAKER_ABSENT = "speaker_absent"
    NETWORK_FAILURE = "network_failure"
    CONTENT_CORRUPTED = "content_corrupted"
    PLATFORM_DOWN = "platform_down"
    TIME_OVERRUN = "time_overrun"
    TECHNICAL_ISSUE = "technical_issue"


@dataclass
class EmergencyScenario:
    """Emergency scenario configuration"""
    scenario_type: EmergencyType
    fallback_content_id: Optional[str] = None
    fallback_message: Optional[str] = None
    auto_trigger: bool = True
    notification_targets: list = None  # SMS/Email targets
    recovery_actions: list = None  # List of recovery steps


class EmergencyManager:
    """
    Manages emergency scenarios and automatic responses.
    
    Features:
    - Predefined scenarios
    - Automatic fallback
    - Operator notifications
    - Recovery procedures
    """
    
    def __init__(self, engine):
        self.engine = engine
        self.event_bus = get_event_bus()
        
        # Scenarios
        self.scenarios: Dict[EmergencyType, EmergencyScenario] = {}
        
        # Callbacks
        self.emergency_callbacks: Dict[EmergencyType, list] = {}
        
        # Active emergencies
        self.active_emergencies: Dict[str, EmergencyType] = {}
        
        self._register_default_scenarios()
        logger.info("EmergencyManager initialized")
    
    def _register_default_scenarios(self):
        """Register default emergency scenarios."""
        # Speaker absent
        self.register_scenario(EmergencyScenario(
            scenario_type=EmergencyType.SPEAKER_ABSENT,
            fallback_message="Speaker is currently unavailable. Please wait...",
            auto_trigger=True,
            recovery_actions=["Display message", "Play sponsor logo", "Notify coordinator"]
        ))
        
        # Network failure
        self.register_scenario(EmergencyScenario(
            scenario_type=EmergencyType.NETWORK_FAILURE,
            fallback_message="Network connectivity issue. Switching to offline mode...",
            auto_trigger=True,
            recovery_actions=["Switch to local playback", "Queue content", "Retry connection"]
        ))
        
        # Content corrupted
        self.register_scenario(EmergencyScenario(
            scenario_type=EmergencyType.CONTENT_CORRUPTED,
            fallback_message="Content unavailable. Loading alternate content...",
            auto_trigger=True,
            recovery_actions=["Load backup content", "Notify operator", "Log incident"]
        ))
    
    def register_scenario(self, scenario: EmergencyScenario):
        """Register emergency scenario."""
        self.scenarios[scenario.scenario_type] = scenario
        logger.info(f"Registered emergency scenario: {scenario.scenario_type.value}")
    
    def set_fallback_content(self, scenario_type: EmergencyType, content_id: str):
        """Set fallback content for scenario."""
        if scenario_type in self.scenarios:
            self.scenarios[scenario_type].fallback_content_id = content_id
            logger.info(f"Set fallback content for {scenario_type.value}: {content_id}")
    
    async def trigger_emergency(
        self,
        scenario_type: EmergencyType,
        context: Optional[Dict] = None,
        manual: bool = False
    ) -> bool:
        """
        Trigger emergency scenario.
        
        Args:
            scenario_type: Type of emergency
            context: Additional context
            manual: Whether manually triggered by operator
        
        Returns:
            True if handled successfully
        """
        logger.warning(f"🚨 Emergency triggered: {scenario_type.value} (manual={manual})")
        
        scenario = self.scenarios.get(scenario_type)
        if not scenario:
            logger.error(f"Unknown scenario: {scenario_type.value}")
            return False
        
        # Generate emergency ID
        emergency_id = f"emg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.active_emergencies[emergency_id] = scenario_type
        
        # Emit event
        self.event_bus.publish(Event(
            event_type=EventType.EMERGENCY_OVERRIDE,
            data={
                'emergency_id': emergency_id,
                'scenario_type': scenario_type.value,
                'manual': manual,
                'context': context or {}
            },
            source='EmergencyManager'
        ))
        
        # Execute response
        success = await self._execute_emergency_response(scenario, context or {})
        
        # Call callbacks
        if scenario_type in self.emergency_callbacks:
            for callback in self.emergency_callbacks[scenario_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(scenario, context)
                    else:
                        callback(scenario, context)
                except Exception as e:
                    logger.error(f"Error in emergency callback: {e}")
        
        return success
    
    async def _execute_emergency_response(
        self,
        scenario: EmergencyScenario,
        context: Dict
    ) -> bool:
        """Execute emergency response actions."""
        try:
            # 1. Stop current playback if needed
            if scenario.scenario_type in [EmergencyType.CONTENT_CORRUPTED, EmergencyType.TECHNICAL_ISSUE]:
                await self.engine.emergency_stop()
            
            # 2. Play fallback content if available
            if scenario.fallback_content_id:
                await self.engine.schedule_content(
                    content_id=scenario.fallback_content_id,
                    start_time=datetime.now(),
                    platforms=['hall', 'skyroom'],
                    priority='emergency'
                )
                logger.info(f"Playing fallback content: {scenario.fallback_content_id}")
            
            # 3. Display message
            if scenario.fallback_message:
                # Emit event for UI to display
                self.event_bus.publish(Event(
                    event_type=EventType.EMERGENCY_MESSAGE,
                    data={'message': scenario.fallback_message},
                    source='EmergencyManager'
                ))
            
            # 4. Execute recovery actions
            for action in (scenario.recovery_actions or []):
                logger.info(f"Recovery action: {action}")
            
            return True
            
        except Exception as e:
            logger.error(f"Emergency response failed: {e}", exc_info=True)
            return False
    
    def resolve_emergency(self, emergency_id: str):
        """Mark emergency as resolved."""
        if emergency_id in self.active_emergencies:
            scenario_type = self.active_emergencies.pop(emergency_id)
            logger.info(f"Emergency resolved: {emergency_id} ({scenario_type.value})")
            
            self.event_bus.publish(Event(
                event_type=EventType.EMERGENCY_RESOLVED,
                data={'emergency_id': emergency_id},
                source='EmergencyManager'
            ))
    
    def on_emergency(self, scenario_type: EmergencyType, callback: Callable):
        """Register callback for emergency type."""
        if scenario_type not in self.emergency_callbacks:
            self.emergency_callbacks[scenario_type] = []
        self.emergency_callbacks[scenario_type].append(callback)
    
    def get_active_emergencies(self) -> Dict[str, EmergencyType]:
        """Get all active emergencies."""
        return self.active_emergencies.copy()

