#!/usr/bin/env python3
"""
Script to fix all repository files to use get_db() instead of global db
"""

import os
import re
from pathlib import Path

def fix_repository_file(file_path):
    """Fix a single repository file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already uses get_db
    if 'get_db' in content:
        return False
    
    # Replace import
    content = content.replace('from app.db.database import db', 'from app.db.database import get_db')
    
    # Find all method definitions and add db = get_db() after the docstring
    def add_get_db_to_method(match):
        method_def = match.group(0)
        # Find the docstring end
        lines = method_def.split('\n')
        result_lines = []
        found_docstring = False
        added_get_db = False
        
        for line in lines:
            result_lines.append(line)
            
            # Check if this line ends a docstring
            if '"""' in line and found_docstring and not added_get_db:
                result_lines.append('        db = get_db()')
                added_get_db = True
            elif '"""' in line and not found_docstring:
                found_docstring = True
            
            # If no docstring, add after method definition
            if not found_docstring and 'def ' in line and ':' in line and not added_get_db:
                if 'await db.' in method_def:  # Only if method uses db
                    result_lines.append('        db = get_db()')
                    added_get_db = True
        
        return '\n'.join(result_lines)
    
    # Pattern to match method definitions with their content until next method or class end
    method_pattern = re.compile(r'    @staticmethod\s*\n    async def [^:]+:.*?(?=\n    @|\n    def |\nclass |\Z)', re.DOTALL)
    content = method_pattern.sub(add_get_db_to_method, content)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    """Fix all repository files"""
    repo_dir = Path(__file__).parent / 'app' / 'db' / 'repositories'
    
    for file_path in repo_dir.glob('*.py'):
        if file_path.name == '__init__.py':
            continue
            
        print(f"Fixing {file_path.name}...")
        try:
            fixed = fix_repository_file(file_path)
            if fixed:
                print(f"  ✓ Fixed {file_path.name}")
            else:
                print(f"  - Skipped {file_path.name} (already uses get_db)")
        except Exception as e:
            print(f"  ✗ Error fixing {file_path.name}: {e}")

if __name__ == '__main__':
    main()