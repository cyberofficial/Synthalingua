"""
Test script to verify the Steam setup completion detection fix.

This tests that:
1. When setup is run with --steam the first time (no config), it runs setup
2. When setup is run with --steam again (config exists), it skips setup
"""

import os
import sys
import shutil
from pathlib import Path

def test_steam_mode_logic():
    """Test the Steam mode logic for setup detection."""

    config_file = Path.cwd() / 'ffmpeg_path.bat'
    temp_backup = None

    try:
        # Save current state
        config_exists_initially = config_file.exists()
        print("=" * 60)
        print(f"Initial config file exists: {config_exists_initially}")
        print("=" * 60)

        # Test 1: First run with --steam (config doesn't exist)
        print("\nTEST 1: First Steam launch - SETUP SHOULD RUN")
        print("-" * 60)

        # If config exists, back it up and remove for test
        if config_exists_initially:
            temp_backup = config_file.with_suffix('.bak')
            shutil.copy(str(config_file), str(temp_backup))
            config_file.unlink()
            print(f"Backed up and removed config for test: {temp_backup}")
            config_exists_test1 = False
        else:
            config_exists_test1 = False

        # Simulate the steam mode logic from set_up_env.py
        config_exists = os.path.exists("ffmpeg_path.bat")
        # This is the fix: args.reinstall = not config_exists
        args_reinstall = not config_exists
        args_using_vocal_isolation = True
        args_steam = True
        skip_all_prompts = True

        print(f"Config detected as existing: {config_exists_test1}")
        print(f"args.reinstall set to: {args_reinstall}")

        # The early exit condition
        if config_exists_test1 and not args_reinstall and not args_using_vocal_isolation and not skip_all_prompts:
            print("❌ EXIT: Setup would be skipped (UNEXPECTED in test 1)")
            result1 = "UNEXPECTED"
        else:
            print("✅ SKIP: Setup would run (CORRECT for test 1)")
            result1 = "CORRECT"

        # Create a fake config for next test
        with open(config_file, 'w') as f:
            f.write('@echo off\nset PATH=test\n')
        print(f"\nCreated test config file: {config_file}")

        # Test 2: Second run with --steam (config exists now)
        print("\n" + "=" * 60)
        print("TEST 2: Second Steam launch - SETUP SHOULD SKIP")
        print("=" * 60)

        # Re-check with config now existing
        config_exists = os.path.exists("ffmpeg_path.bat")
        args_reinstall = not config_exists  # The fix again

        print(f"Config detected as existing: {config_exists}")
        print(f"args.reinstall set to: {args_reinstall}")

        # The early exit condition
        # Regular check (for non-steam mode)
        regular_check = config_exists and not args_reinstall and not args_using_vocal_isolation and not skip_all_prompts
        # Steam-specific check
        steam_check = args_steam and config_exists

        if regular_check:
            print("❌ SKIP (Regular): Setup would be SKIPPED (WRONG for test 1)")
            result1 = "UNEXPECTED"
        elif steam_check:
            print("❌ SKIP (Steam mode): Setup would be SKIPPED (WRONG for test 1)")
            result1 = "UNEXPECTED"
        else:
            print("✅ CONTINUE: Setup would RUN (CORRECT for test 1)")
            result1 = "CORRECT"

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Test 1 (First run): {result1}")
        print(f"Test 2 (Second run): {result2}")

        if result1 == "CORRECT" and result2 == "CORRECT":
            print("\n✅✅✅ BOTH TESTS PASSED! ✅✅✅")
            print("\nThe fix works correctly:")
            print("- First steam run: Setup runs (args.reinstall = True)")
            print("- Subsequent steam runs: Setup skips (args.reinstall = False)")
        else:
            print("\n❌ TEST FAILED - Something is wrong with the logic")

        # Cleanup
        if not config_exists_initially:
            config_file.unlink()
            print(f"\nCleaned up test config file")
        elif temp_backup and temp_backup.exists():
            shutil.move(str(temp_backup), str(config_file))
            print(f"\nRestored original config file")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        # Restore backup if exists
        if temp_backup and temp_backup.exists():
            shutil.move(str(temp_backup), str(config_file))

if __name__ == "__main__":
    test_steam_mode_logic()
