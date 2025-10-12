"""
Smart Database Updater for Org Chart with Cooldown
Only updates when needed, prevents redundant updates within cooldown period
"""

import sqlite3
from datetime import datetime, timedelta
import threading
import time
from typing import Callable, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== GLOBAL VARIABLES ====================

# Cooldown period in seconds (if update happened within this time, skip)
UPDATE_COOLDOWN_SECONDS = 10  # 10 seconds cooldown

# Database path
DB_PATH = "System-Info/employee_hierarchy.db"

# Last update timestamp
LAST_UPDATE_TIME = None

# Total update count
UPDATE_COUNT = 0

# Lock for thread-safe operations
_update_lock = threading.Lock()

# Flag to track if update is in progress
UPDATE_IN_PROGRESS = False


# ==================== SMART UPDATER CLASS ====================

class SmartDBUpdater:
    """
    Smart database updater that only updates when needed
    Prevents redundant updates within cooldown period
    """
    
    def __init__(self, db_path: str = DB_PATH, cooldown_seconds: int = UPDATE_COOLDOWN_SECONDS):
        """
        Initialize smart updater
        
        Args:
            db_path: Path to database
            cooldown_seconds: Minimum seconds between updates
        """
        self.db_path = db_path
        self.cooldown_seconds = cooldown_seconds
        self.update_function: Optional[Callable] = None
        
    def set_update_function(self, func: Callable):
        """Set the function to be called when update is needed"""
        self.update_function = func
        logger.info(f"Update function registered: {func.__name__}")
    
    def should_update(self) -> bool:
        """
        Check if database should be updated based on cooldown period
        
        Returns:
            True if update is needed, False if within cooldown period
        """
        global LAST_UPDATE_TIME
        
        if LAST_UPDATE_TIME is None:
            return True  # First time, always update
        
        time_since_last_update = (datetime.now() - LAST_UPDATE_TIME).total_seconds()
        
        if time_since_last_update < self.cooldown_seconds:
            logger.info(f"⏳ Skipping update - Last update was {time_since_last_update:.1f}s ago (cooldown: {self.cooldown_seconds}s)")
            return False
        
        return True
    
    def update_now(self, force: bool = False, user_id: str = None) -> bool:
        """
        Trigger database update if needed
        
        Args:
            force: If True, ignore cooldown and force update
            user_id: Optional user ID who triggered the update
            
        Returns:
            True if update was performed, False if skipped
        """
        global LAST_UPDATE_TIME, UPDATE_COUNT, UPDATE_IN_PROGRESS, _update_lock
        
        # Thread-safe check and update
        with _update_lock:
            # Check if update is already in progress
            if UPDATE_IN_PROGRESS:
                logger.info("⏳ Update already in progress, skipping...")
                return False
            
            # Check if update is needed (unless forced)
            if not force and not self.should_update():
                return False
            
            # Mark update as in progress
            UPDATE_IN_PROGRESS = True
        
        try:
            # Call the update function
            if self.update_function is None:
                raise Exception("No update function registered!")
            
            user_msg = f" (triggered by {user_id})" if user_id else ""
            logger.info(f"🔄 Starting org chart database update{user_msg}...")
            
            # Execute the update
            result = self.update_function()
            
            # Update global state
            with _update_lock:
                LAST_UPDATE_TIME = datetime.now()
                UPDATE_COUNT += 1
                UPDATE_IN_PROGRESS = False
            
            logger.info(f"✅ Update completed successfully (Total updates: {UPDATE_COUNT})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Update failed: {str(e)}")
            with _update_lock:
                UPDATE_IN_PROGRESS = False
            raise
    
    def get_status(self) -> dict:
        """
        Get current updater status
        
        Returns:
            Dict with status information
        """
        global LAST_UPDATE_TIME, UPDATE_COUNT, UPDATE_IN_PROGRESS
        
        status = {
            'last_update': LAST_UPDATE_TIME.strftime('%Y-%m-%d %H:%M:%S') if LAST_UPDATE_TIME else 'Never',
            'update_count': UPDATE_COUNT,
            'cooldown_seconds': self.cooldown_seconds,
            'update_in_progress': UPDATE_IN_PROGRESS,
            'can_update_now': self.should_update(),
            'seconds_since_last_update': (datetime.now() - LAST_UPDATE_TIME).total_seconds() if LAST_UPDATE_TIME else None
        }
        
        return status


# ==================== GLOBAL INSTANCE ====================

# Global updater instance (singleton pattern)
_UPDATER_INSTANCE: Optional[SmartDBUpdater] = None


def get_updater(cooldown_seconds: int = UPDATE_COOLDOWN_SECONDS) -> SmartDBUpdater:
    """
    Get or create the global updater instance
    
    Args:
        cooldown_seconds: Cooldown period in seconds
        
    Returns:
        SmartDBUpdater instance
    """
    global _UPDATER_INSTANCE
    
    if _UPDATER_INSTANCE is None:
        _UPDATER_INSTANCE = SmartDBUpdater(
            db_path=DB_PATH,
            cooldown_seconds=cooldown_seconds
        )
        logger.info(f"📦 Created new SmartDBUpdater instance (cooldown: {cooldown_seconds}s)")
    
    return _UPDATER_INSTANCE


def trigger_update(force: bool = False, user_id: str = None) -> bool:
    """
    Trigger an update using the global updater
    
    Args:
        force: Force update even if within cooldown
        user_id: User who triggered the update
        
    Returns:
        True if update was performed
    """
    updater = get_updater()
    return updater.update_now(force=force, user_id=user_id)


def get_update_status() -> dict:
    """
    Get current update status
    
    Returns:
        Status dictionary
    """
    updater = get_updater()
    return updater.get_status()


# ==================== HELPER FUNCTIONS ====================

def force_update_now(user_id: str = None) -> bool:
    """
    Force an immediate update, ignoring cooldown
    
    Args:
        user_id: User who triggered the update
        
    Returns:
        True if update succeeded
    """
    return trigger_update(force=True, user_id=user_id)


def reset_update_timer():
    """Reset the update timer (for testing/debugging)"""
    global LAST_UPDATE_TIME
    LAST_UPDATE_TIME = None
    logger.info("🔄 Update timer reset")
