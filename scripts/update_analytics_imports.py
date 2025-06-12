#!/usr/bin/env python3
"""
Script to update import statements in analytics package to use shared components.
"""

import os
import re
import glob

def update_file_imports(file_path):
    """Update imports in a single file."""
    print(f"Updating imports in {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Add shared path import if not already present
    if 'sys.path.append' not in content and ('from database_connection' in content or 'from auth' in content):
        imports_section = """# Import from shared components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

"""
        # Insert after existing imports but before first from statement
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i
                break
        
        if insert_pos > 0:
            lines.insert(insert_pos, imports_section.strip())
            content = '\n'.join(lines)
    
    # Update database_connection imports
    content = re.sub(
        r'from database_connection import',
        'from database.database_connection import',
        content
    )
    
    # Update relative database_connection imports
    content = re.sub(
        r'from \.database_connection import',
        'from database.database_connection import',
        content
    )
    
    # Update auth imports (but not analytics.auth)
    content = re.sub(
        r'from auth import',
        'from auth.auth import',
        content
    )
    
    # Fix any analytics.auth imports that shouldn't be there
    content = re.sub(
        r'from analytics\.auth import',
        'from auth.auth import',
        content
    )
    
    # Handle try/except auth imports
    content = re.sub(
        r'try:\s*\n\s*from analytics\.auth import (.*?)\s*\nexcept ImportError:\s*\n\s*from auth import \1',
        r'from auth.auth import \1',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Updated {file_path}")
    else:
        print(f"  - No changes needed for {file_path}")

def main():
    """Update all Python files in the analytics package."""
    analytics_dir = "packages/analytics"
    
    if not os.path.exists(analytics_dir):
        print(f"Analytics directory not found: {analytics_dir}")
        return
    
    print("🔄 Updating imports in analytics package...")
    
    # Find all Python files
    python_files = glob.glob(os.path.join(analytics_dir, "*.py"))
    python_files.extend(glob.glob(os.path.join(analytics_dir, "**", "*.py"), recursive=True))
    
    for file_path in python_files:
        # Skip __pycache__ and .git directories
        if '__pycache__' in file_path or '.git' in file_path:
            continue
            
        update_file_imports(file_path)
    
    print("✅ Import updates complete!")
    print("\n📝 Next steps:")
    print("1. Test the analytics dashboard: cd packages/analytics && python db_dashboard.py")
    print("2. Fix any remaining import issues manually")
    print("3. Update any hardcoded paths in configuration files")

if __name__ == "__main__":
    main() 