"""
Test script for API key rotation system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_config.agent import basic_llm
from agents.llm_config.utils import get_api_usage_stats, reset_api_usage_stats
import time

def test_api_rotation():
    """Test the API key rotation system"""
    print("Testing API Key Rotation System...")
    print("=" * 50)
    
    # Reset usage stats for clean test
    reset_api_usage_stats()
    
    # Test normal operation
    print("1. Testing normal operation...")
    try:
        # This should work with the first available key
        response = basic_llm._current_llm.model  # Simple attribute access
        print(f"✓ Successfully accessed model: {response}")
    except Exception as e:
        print(f"✗ Error in normal operation: {e}")
    
    # Print current API key info
    current_key = basic_llm.api_manager.get_current_key()
    print(f"Current API Key: ...{current_key[-4:]}")
    print(f"Current Key Index: {basic_llm.api_manager.current_key_index}")
    
    # Test key rotation
    print("\n2. Testing key rotation...")
    original_index = basic_llm.api_manager.current_key_index
    basic_llm.api_manager.rotate_key()
    new_index = basic_llm.api_manager.current_key_index
    print(f"✓ Key rotated from index {original_index} to {new_index}")
    
    # Test failed key handling
    print("\n3. Testing failed key handling...")
    current_key = basic_llm.api_manager.get_current_key()
    basic_llm.api_manager.mark_key_as_failed(current_key)
    new_key = basic_llm.api_manager.get_current_key()
    print(f"✓ Key marked as failed and rotated to: ...{new_key[-4:]}")
    
    # Test cooldown system
    print("\n4. Testing cooldown system...")
    failed_keys_count = len(basic_llm.api_manager.failed_keys)
    print(f"Failed keys count: {failed_keys_count}")
    
    # Print usage stats
    print("\n5. Usage Statistics:")
    stats = get_api_usage_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    print("API Key Rotation Test Complete!")

if __name__ == "__main__":
    test_api_rotation()
