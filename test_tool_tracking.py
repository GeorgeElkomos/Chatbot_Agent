"""
Test script to verify tool tracking in iteration_tracker.py
Tests the query: "give me the data for the greatest expense"
"""

import os
import sys

# Set UTF-8 encoding for Windows console before any imports
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")

import json
from agents.registry.registration import register_agents
from remove_emoji import remove_emoji
from orchestrator import orchestrate

def test_tool_tracking():
    """Test tool tracking with a specific query"""
    remove_emoji()
    register_agents()
    
    print("=" * 80)
    print("🧪 TESTING TOOL TRACKING")
    print("=" * 80)
    print()
    
    # Test query
    test_query = "give me the data for the greatest expense"
    
    print(f"📝 Test Query: {test_query}")
    print()
    print("-" * 80)
    print()
    
    # Execute orchestrator
    conversation_history = []
    response = orchestrate(test_query, conversation_history, logs=False)
    
    print()
    print("=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)
    print()
    
    # Print response
    print("📊 Response:")
    print(json.dumps(response, indent=2))
    print()
    
    # Check history.json for tool tracking
    print("-" * 80)
    print("🔍 Checking history.json for tool tracking...")
    print("-" * 80)
    print()
    
    try:
        with open("ai-output/history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
        
        # Find FusionAnalyticsAgent entries
        fusion_entries = [entry for entry in history if entry.get("agent") == "FusionAnalyticsAgent"]
        
        if fusion_entries:
            print(f"✅ Found {len(fusion_entries)} FusionAnalyticsAgent entry/entries")
            print()
            
            for idx, entry in enumerate(fusion_entries, 1):
                print(f"Entry {idx}:")
                track_internal = entry.get("track_internal", [])
                
                if not track_internal:
                    print("  ⚠️  No track_internal data")
                    continue
                
                for iteration in track_internal:
                    iter_num = iteration.get("iteration_number")
                    tool_called = iteration.get("tool_called")
                    tool_args = iteration.get("tool_args")
                    tool_output = iteration.get("tool_output")
                    
                    print(f"  Iteration {iter_num}:")
                    if tool_called:
                        print(f"    ✅ Tool Called: {tool_called}")
                        print(f"    ✅ Tool Args: {json.dumps(tool_args, indent=6)}")
                        print(f"    ✅ Tool Output: {tool_output[:100] if tool_output else 'None'}...")
                    else:
                        print(f"    ❌ Tool Called: None")
                        print(f"    ❌ Tool Args: None")
                        print(f"    ❌ Tool Output: None")
                    print()
        else:
            print("❌ No FusionAnalyticsAgent entries found in history")
    
    except FileNotFoundError:
        print("❌ history.json file not found")
    except Exception as e:
        print(f"❌ Error reading history: {e}")
    
    print()
    print("=" * 80)
    print("🎯 TEST SUMMARY")
    print("=" * 80)
    print()
    print("If you see '✅ Tool Called', '✅ Tool Args', and '✅ Tool Output'")
    print("in the iterations above, then tool tracking is working correctly!")
    print()

if __name__ == "__main__":
    test_tool_tracking()
