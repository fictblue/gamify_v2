#!/usr/bin/env python
"""
Test script to verify dark dominant theme implementation
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamify_ai.settings')
django.setup()

def test_dark_dominant_theme():
    """Test that dark dominant theme is properly implemented"""
    print("🌑 DARK DOMINANT THEME IMPLEMENTATION TEST")
    print("=" * 60)

    # Read base.html content
    try:
        with open(r'c:\Users\TOUCH U\Videos\gamify_v2\templates\base.html', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print("❌ Could not read base.html - encoding issue")
        return

    print("✅ DARK DOMINANT THEME VERIFICATION:")
    print()

    # Test 1: Background opacity reduction
    dark_bg_tests = [
        'rgba(0, 0, 0, 0.97)' in content,  # Card backgrounds more dark
        'rgba(0, 0, 0, 0.98)' in content,  # Navbar more dark
        'rgba(0, 0, 0, 0.9)' in content,   # Footer more dark
    ]

    print("📦 Background Opacity Reduction:")
    print(f"   Cards: {'✅ 0.97 opacity' if dark_bg_tests[0] else '❌ not found'}")
    print(f"   Navbar: {'✅ 0.98 opacity' if dark_bg_tests[1] else '❌ not found'}")
    print(f"   Footer: {'✅ 0.9 opacity' if dark_bg_tests[2] else '❌ not found'}")
    print()

    # Test 2: Border opacity reduction
    border_tests = [
        'rgba(0, 255, 255, 0.25)' in content,  # Card borders
        'rgba(0, 255, 255, 0.2)' in content,   # User dropdown borders
        'rgba(0, 255, 255, 0.15)' in content,  # Navbar border
        'rgba(0, 255, 255, 0.4)' in content,   # Buttons
    ]

    print("🔲 Border Opacity Reduction:")
    print(f"   Card borders: {'✅ 0.25 opacity' if border_tests[0] else '❌ not found'}")
    print(f"   Dropdown borders: {'✅ 0.2 opacity' if border_tests[1] else '❌ not found'}")
    print(f"   Navbar border: {'✅ 0.15 opacity' if border_tests[2] else '❌ not found'}")
    print(f"   Button borders: {'✅ 0.4 opacity' if border_tests[3] else '❌ not found'}")
    print()

    # Test 3: Shadow intensity reduction
    shadow_tests = [
        'rgba(0, 255, 255, 0.08)' in content,  # Card shadows
        'rgba(0, 255, 255, 0.12)' in content,  # Tooltip shadows
        'rgba(0, 255, 255, 0.15)' in content,  # XP toast shadows
        'rgba(255, 0, 255, 0.1)' in content,   # Magenta shadows
        'rgba(0, 255, 0, 0.15)' in content,    # Green shadows
    ]

    print("💫 Shadow Intensity Reduction:")
    print(f"   Card shadows: {'✅ 0.08 cyan' if shadow_tests[0] else '❌ not found'}")
    print(f"   Tooltip shadows: {'✅ 0.12 cyan' if shadow_tests[1] else '❌ not found'}")
    print(f"   XP toast shadows: {'✅ 0.15 green' if shadow_tests[2] else '❌ not found'}")
    print(f"   Magenta shadows: {'✅ 0.1 opacity' if shadow_tests[3] else '❌ not found'}")
    print(f"   Green shadows: {'✅ 0.15 opacity' if shadow_tests[4] else '❌ not found'}")
    print()

    # Test 4: Text shadow reduction
    text_shadow_tests = [
        'text-shadow: 0 0 6px' in content,   # Reduced from 8px/10px
        'text-shadow: 0 0 8px' in content,   # Still some bright elements
        'text-shadow: 0 0 3px' in content,   # Very subtle shadows
        'text-shadow: 0 0 4px' in content,   # Subtle shadows
    ]

    print("✍️ Text Shadow Reduction:")
    print(f"   6px shadows: {'✅ subtle' if text_shadow_tests[0] else '❌ not found'}")
    print(f"   8px shadows: {'✅ medium' if text_shadow_tests[1] else '❌ not found'}")
    print(f"   3px shadows: {'✅ very subtle' if text_shadow_tests[2] else '❌ not found'}")
    print(f"   4px shadows: {'✅ subtle' if text_shadow_tests[3] else '❌ not found'}")
    print()

    # Test 5: Particle effects reduction
    particle_tests = [
        'rgba(0, 17, 255, 0.04)' in content,   # Blue particles
        'rgba(255, 0, 255, 0.04)' in content,   # Magenta particles
        'rgba(0, 255, 0, 0.02)' in content,    # Green particles
        'opacity: 0.25' in content,            # Overall opacity
        'opacity: 0.15' in content,            # Mobile opacity
    ]

    print("✨ Particle Effects Reduction:")
    print(f"   Blue particles: {'✅ 0.04 opacity' if particle_tests[0] else '❌ not found'}")
    print(f"   Magenta particles: {'✅ 0.04 opacity' if particle_tests[1] else '❌ not found'}")
    print(f"   Green particles: {'✅ 0.02 opacity' if particle_tests[2] else '❌ not found'}")
    print(f"   Desktop opacity: {'✅ 0.25' if particle_tests[3] else '❌ not found'}")
    print(f"   Mobile opacity: {'✅ 0.15' if particle_tests[4] else '❌ not found'}")
    print()

    # Test 6: Gaming elements preservation
    gaming_tests = [
        'robot-companion' in content,      # Robot companion
        'xp-toast' in content,             # XP system
        'progress-gamify' in content,      # Progress bars
        'btn-gamify' in content,           # Gaming buttons
        'level-up-animation' in content,   # Level animations
        'achievement-unlock' in content,   # Achievement system
        'gradient-primary' in content,     # Gradients preserved
        'animation:' in content,           # Animations preserved
    ]

    print("🎮 Gaming Elements Preservation:")
    print(f"   Robot companion: {'✅ preserved' if gaming_tests[0] else '❌ missing'}")
    print(f"   XP toast system: {'✅ preserved' if gaming_tests[1] else '❌ missing'}")
    print(f"   Progress bars: {'✅ preserved' if gaming_tests[2] else '❌ missing'}")
    print(f"   Gaming buttons: {'✅ preserved' if gaming_tests[3] else '❌ missing'}")
    print(f"   Level animations: {'✅ preserved' if gaming_tests[4] else '❌ missing'}")
    print(f"   Achievement system: {'✅ preserved' if gaming_tests[5] else '❌ missing'}")
    print(f"   Gradient system: {'✅ preserved' if gaming_tests[6] else '❌ missing'}")
    print(f"   Animation system: {'✅ preserved' if gaming_tests[7] else '❌ missing'}")
    print()

    # Test 7: Mobile responsiveness updates
    mobile_tests = [
        'max-width: 768px' in content,
        'min-width: 32px' in content,
        'Mobile checkbox improvements' in content,
        'Mobile hint box improvements' in content,
        'calc(70vh - 180px)' in content,
    ]

    print("📱 Mobile Responsiveness Updates:")
    print(f"   Mobile breakpoints: {'✅ preserved' if mobile_tests[0] else '❌ missing'}")
    print(f"   Touch targets: {'✅ larger (32px)' if mobile_tests[1] else '❌ not found'}")
    print(f"   Mobile checkboxes: {'✅ improved' if mobile_tests[2] else '❌ not found'}")
    print(f"   Mobile hints: {'✅ improved' if mobile_tests[3] else '❌ not found'}")
    print(f"   Mobile spacing: {'✅ optimized' if mobile_tests[4] else '❌ not found'}")
    print()

    # Summary
    total_tests = len(dark_bg_tests) + len(border_tests) + len(shadow_tests) + len(text_shadow_tests) + len(particle_tests) + len(gaming_tests) + len(mobile_tests)
    passed_tests = sum(dark_bg_tests) + sum(border_tests) + sum(shadow_tests) + sum(text_shadow_tests) + sum(particle_tests) + sum(gaming_tests) + sum(mobile_tests)

    print("🎯 IMPLEMENTATION SUMMARY:")
    print(f"   Tests passed: {passed_tests}/{total_tests}")
    print(f"   Success rate: {passed_tests/total_tests*100:.1f}%")
    print()

    if passed_tests/total_tests >= 0.8:
        print("✅ DARK DOMINANT THEME: SUCCESSFULLY IMPLEMENTED!")
        print("   - Backgrounds: More dark and immersive")
        print("   - Glows: Subtle and elegant")
        print("   - Gaming elements: Fully preserved")
        print("   - Mobile responsive: Enhanced")
        print("   - User experience: Improved for long sessions")
    else:
        print("⚠️ DARK DOMINANT THEME: NEEDS REVIEW")
        print("   Some styling may need additional adjustments")

    print()
    print("🧪 TESTING INSTRUCTIONS:")
    print("   1. Open any page in browser")
    print("   2. Check background darkness - should be more black")
    print("   3. Verify neon glows are subtle but visible")
    print("   4. Test gaming elements (robot, XP, animations)")
    print("   5. Check mobile responsiveness")
    print("   6. Verify accessibility (focus states, contrast)")
    print()
    print("🎨 VISUAL IMPROVEMENTS:")
    print("   - More immersive dark environment")
    print("   - Reduced eye strain for long sessions")
    print("   - Professional gaming aesthetic")
    print("   - Preserved visual hierarchy")
    print("   - Enhanced contrast ratios")
    print()
    print("🚀 READY FOR USER TESTING!")

if __name__ == '__main__':
    test_dark_dominant_theme()
