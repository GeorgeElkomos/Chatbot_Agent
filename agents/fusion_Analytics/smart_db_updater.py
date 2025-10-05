"""
Smart Database Updater with Cooldown
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
UPDATE_COOLDOWN_SECONDS = 5  # Change this as needed (e.g., 5, 10, 30 seconds)

# Database path
DB_PATH = "System-Info/expense_reports.db"

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
                logger.warning(f"⏸️  Update already in progress, skipping request from {user_id or 'unknown user'}")
                return False
            
            # Check cooldown (unless forced)
            if not force and not self.should_update():
                logger.info(f"⏭️  Update skipped for {user_id or 'user'} (within cooldown period)")
                return False
            
            # Mark update as in progress
            UPDATE_IN_PROGRESS = True
        
        try:
            # Perform the update
            logger.info(f"🔄 Starting database update (triggered by: {user_id or 'system'})")
            
            if self.update_function:
                self.update_function(self.db_path)
            else:
                logger.warning("No update function set!")
                return False
            
             
            


            # Update global variables
            with _update_lock:
                LAST_UPDATE_TIME = datetime.now()
                UPDATE_COUNT += 1
            
            logger.info(f"✅ Update completed successfully (Update #{UPDATE_COUNT})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during update: {e}", exc_info=True)
            return False
            
        finally:
            # Always release the lock
            with _update_lock:
                UPDATE_IN_PROGRESS = False
    
    def get_time_since_last_update(self) -> Optional[float]:
        """Get seconds since last update"""
        global LAST_UPDATE_TIME
        
        if LAST_UPDATE_TIME is None:
            return None
        
        return (datetime.now() - LAST_UPDATE_TIME).total_seconds()
    
    def get_time_until_next_update(self) -> float:
        """Get seconds until cooldown expires"""
        time_since = self.get_time_since_last_update()
        
        if time_since is None:
            return 0  # Can update now
        
        remaining = self.cooldown_seconds - time_since
        return max(0, remaining)
    
    def get_status(self) -> dict:
        """Get current status"""
        global LAST_UPDATE_TIME, UPDATE_COUNT, UPDATE_IN_PROGRESS
        
        time_since = self.get_time_since_last_update()
        time_until = self.get_time_until_next_update()
        
        return {
            'db_path': self.db_path,
            'cooldown_seconds': self.cooldown_seconds,
            'last_update': LAST_UPDATE_TIME.strftime('%Y-%m-%d %H:%M:%S') if LAST_UPDATE_TIME else 'Never',
            'update_count': UPDATE_COUNT,
            'time_since_last_update': f"{time_since:.1f}s" if time_since else 'N/A',
            'time_until_next_update': f"{time_until:.1f}s" if time_until > 0 else 'Ready',
            'can_update_now': time_until == 0,
            'update_in_progress': UPDATE_IN_PROGRESS
        }
    
    def print_status(self):
        """Print current status"""
        status = self.get_status()
        
        print("\n" + "=" * 70)
        print("SMART DATABASE UPDATER STATUS")
        print("=" * 70)
        print(f"Database:           {status['db_path']}")
        print(f"Cooldown Period:    {status['cooldown_seconds']} seconds")
        print(f"Last Update:        {status['last_update']}")
        print(f"Time Since Update:  {status['time_since_last_update']}")
        print(f"Time Until Ready:   {status['time_until_next_update']}")
        print(f"Total Updates:      {status['update_count']}")
        print(f"Update In Progress: {'Yes 🔄' if status['update_in_progress'] else 'No'}")
        print(f"Can Update Now:     {'Yes ✅' if status['can_update_now'] else 'No ⏳'}")
        print("=" * 70 + "\n")


# ==================== GLOBAL INSTANCE (SINGLETON) ====================

# Global updater instance - use this throughout your application
_global_updater = None

def get_updater(cooldown_seconds: int = UPDATE_COOLDOWN_SECONDS) -> SmartDBUpdater:
    """
    Get or create global updater instance
    
    Args:
        cooldown_seconds: Cooldown period in seconds
        
    Returns:
        Global SmartDBUpdater instance
    """
    global _global_updater
    
    if _global_updater is None:
        _global_updater = SmartDBUpdater(cooldown_seconds=cooldown_seconds)
    
    return _global_updater


def trigger_update(user_id: str = None, force: bool = False) -> bool:
    """
    Convenient function to trigger database update
    
    Args:
        user_id: ID of user who triggered the update
        force: Force update even if within cooldown
        
    Returns:
        True if update was performed, False if skipped
    """
    updater = get_updater()
    return updater.update_now(force=force, user_id=user_id)


def get_update_status() -> dict:
    """Get current update status"""
    updater = get_updater()
    return updater.get_status()


def print_update_status():
    """Print current update status"""
    updater = get_updater()
    updater.print_status()


# ==================== EXAMPLE UPDATE FUNCTIONS ====================

def refresh_expense_data(db_path: str):
    """Example update function - replace with your logic"""
    logger.info("Executing database refresh...")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Your update logic here
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(reimbursable_amount) as total_amount
            FROM expense_report_data
        """)
        
        result = cursor.fetchone()
        logger.info(f"  Total Records: {result['total_records']}")
        logger.info(f"  Total Amount: ${result['total_amount']:.2f}")
        
        conn.close()
        
        # Add your custom update logic:
        # - Fetch from API
        # - Recalculate aggregations
        # - Update cached data
        # - Refresh ML models
        # etc.
    except Exception as e:
        logger.error(f"Error in refresh_expense_data: {e}")


# ==================== USAGE EXAMPLES ====================

def simulate_multiple_users():
    """Simulate multiple users trying to update at different times"""
    print("\n" + "=" * 70)
    print("SIMULATING MULTIPLE USERS WITH COOLDOWN")
    print("=" * 70)
    
    # Initialize updater with 5-second cooldown
    updater = get_updater(cooldown_seconds=5)
    updater.set_update_function(refresh_expense_data)
    
    print("\n📋 Scenario:")
    print("   Cooldown: 5 seconds")
    print("   User 1 updates at T=0")
    print("   User 2 updates at T=2 (should skip)")
    print("   User 3 updates at T=6 (should execute)")
    print("\n")
    
    # User 1 performs action (T=0)
    print("⏰ T=0: User 1 performs action")
    result = trigger_update(user_id="User_1")
    print(f"   Result: {'✅ Updated' if result else '⏭️ Skipped'}\n")
    time.sleep(2)
    
    # User 2 performs action (T=2)
    print("⏰ T=2: User 2 performs same action (2 seconds later)")
    result = trigger_update(user_id="User_2")
    print(f"   Result: {'✅ Updated' if result else '⏭️ Skipped'}\n")
    time.sleep(1)
    
    # User 3 tries (T=3)
    print("⏰ T=3: User 3 tries (3 seconds later)")
    result = trigger_update(user_id="User_3")
    print(f"   Result: {'✅ Updated' if result else '⏭️ Skipped'}\n")
    time.sleep(3)
    
    # User 4 tries (T=6)
    print("⏰ T=6: User 4 tries (6 seconds later - cooldown expired)")
    result = trigger_update(user_id="User_4")
    print(f"   Result: {'✅ Updated' if result else '⏭️ Skipped'}\n")
    
    # Show final status
    print_update_status()


def example_chatbot_integration():
    """Example: Integration with chatbot"""
    print("\n" + "=" * 70)
    print("CHATBOT INTEGRATION EXAMPLE")
    print("=" * 70)
    
    # Initialize updater
    updater = get_updater(cooldown_seconds=5)
    updater.set_update_function(refresh_expense_data)
    
    print("\n🤖 Chatbot Scenario:")
    print("   3 users submit expense reports within 10 seconds")
    print("   Database should only update once (with cooldown)\n")
    
    # Simulate users submitting reports
    users = ["Alice", "Bob", "Charlie"]
    
    for i, user in enumerate(users):
        print(f"\n👤 {user} submits an expense report")
        
        # User submits report (your business logic here)
        print(f"   Processing {user}'s report...")
        
        # Trigger database update
        updated = trigger_update(user_id=user)
        
        if updated:
            print(f"   ✅ Database updated for {user}'s submission")
        else:
            print(f"   ⏭️ Database not updated (within cooldown)")
        
        # Show status
        status = get_update_status()
        print(f"   ⏱️  Time until next update available: {status['time_until_next_update']}")
        
        # Simulate time between user actions
        if i < len(users) - 1:
            time.sleep(2)  # 2 seconds between users
    
    print("\n")
    print_update_status()


def example_force_update():
    """Example: Force update ignoring cooldown"""
    print("\n" + "=" * 70)
    print("FORCE UPDATE EXAMPLE")
    print("=" * 70)
    
    updater = get_updater(cooldown_seconds=10)
    updater.set_update_function(refresh_expense_data)
    
    print("\n📋 Scenario: Critical update needed\n")
    
    # Normal update
    print("1️⃣ Normal update")
    trigger_update(user_id="User_1")
    time.sleep(2)
    
    # Try normal update (should skip)
    print("\n2️⃣ Try update 2 seconds later (should skip)")
    trigger_update(user_id="User_2")
    
    # Force update
    print("\n3️⃣ FORCE update (admin override)")
    trigger_update(user_id="Admin", force=True)
    
    print("\n")
    print_update_status()


# ==================== MAIN ====================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SMART DATABASE UPDATER - ON-DEMAND WITH COOLDOWN")
    print("=" * 70)
    
    # Run examples
    simulate_multiple_users()
    
    print("\n" + "="*70)
    time.sleep(2)
    
    example_chatbot_integration()
    
    print("\n" + "="*70)
    time.sleep(2)
    
    example_force_update()
    
    print("\n" + "=" * 70)
    print("✅ ALL EXAMPLES COMPLETED")
    print("=" * 70 + "\n")
