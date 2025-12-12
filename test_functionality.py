#!/usr/bin/env python
"""
Test script to verify the collapsible cards functionality.
This script checks if the grouped answers page has the correct functionality.
"""

def test_collapsible_cards():
    """
    Test that the grouped answers page has collapsible cards functionality.
    """
    print("Testing collapsible cards functionality...")
    
    # Check that the template has been updated with Bootstrap collapse functionality
    template_path = "/workspace/templates/tasks/grouped_answers.html"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Check for Bootstrap data attributes
    has_data_bs_toggle = 'data-bs-toggle' in template_content
    has_data_bs_target = 'data-bs-target' in template_content
    has_collapse_class = 'card-body collapse' in template_content
    
    # Check for Font Awesome icons
    has_chevron_icons = 'fa-chevron-down' in template_content and 'fa-chevron-up' in template_content
    
    # Check for Bootstrap parent attribute
    has_bs_parent = 'data-bs-parent' in template_content
    
    print(f"✓ Has data-bs-toggle attribute: {has_data_bs_toggle}")
    print(f"✓ Has data-bs-target attribute: {has_data_bs_target}")
    print(f"✓ Has collapse class: {has_collapse_class}")
    print(f"✓ Has chevron icons: {has_chevron_icons}")
    print(f"✓ Has data-bs-parent attribute: {has_bs_parent}")
    
    # Check for event listeners for Bootstrap collapse
    has_show_listener = 'show.bs.collapse' in template_content
    has_hide_listener = 'hide.bs.collapse' in template_content
    
    print(f"✓ Has show.bs.collapse listener: {has_show_listener}")
    print(f"✓ Has hide.bs.collapse listener: {has_hide_listener}")
    
    # Check if base template has Font Awesome
    base_template_path = "/workspace/templates/base.html"
    with open(base_template_path, 'r', encoding='utf-8') as f:
        base_content = f.read()
    
    has_font_awesome = 'font-awesome' in base_content.lower() or 'fas fa-' in base_content
    
    print(f"✓ Font Awesome included in base template: {has_font_awesome}")
    
    all_checks = [
        has_data_bs_toggle,
        has_data_bs_target,
        has_collapse_class,
        has_chevron_icons,
        has_bs_parent,
        has_show_listener,
        has_hide_listener,
        has_font_awesome
    ]
    
    if all(all_checks):
        print("\n✅ All collapsible cards functionality checks passed!")
        print("Cards should now be collapsed by default and expand when clicked.")
        return True
    else:
        print("\n❌ Some checks failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    test_collapsible_cards()