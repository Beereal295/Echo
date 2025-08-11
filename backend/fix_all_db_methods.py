#!/usr/bin/env python3
"""
Script to add 'db = get_db()' to all methods that use 'await db.' 
"""

import os
import re
from pathlib import Path

def fix_file(file_path):
    """Fix a single Python file"""
    print(f"Processing {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Check if this line defines an async method
        if ('async def ' in line and 
            ':' in line and 
            ('    def ' in line or '@staticmethod' in lines[i-1] if i > 0 else False)):
            
            # Look ahead to see if this method uses 'await db.'
            method_uses_db = False
            j = i + 1
            indent_level = len(line) - len(line.lstrip())
            
            # Look for 'await db.' in the method body
            while j < len(lines):
                next_line = lines[j]
                if next_line.strip() == '':
                    j += 1
                    continue
                
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If we've reached the same or lower indent level, we've left the method
                if next_line.strip() and next_indent <= indent_level and 'def ' in next_line:
                    break
                
                if 'await db.' in next_line:
                    method_uses_db = True
                    break
                    
                j += 1
            
            # If method uses db, add 'db = get_db()' after docstring or method definition
            if method_uses_db:
                # Look for end of docstring or just add after method definition
                k = i + 1
                added_get_db = False
                
                while k < len(lines) and not added_get_db:
                    next_line = lines[k]
                    
                    # Skip empty lines
                    if not next_line.strip():
                        new_lines.append(next_line)
                        k += 1
                        continue
                    
                    # If we find a docstring end, add after it
                    if '"""' in next_line and k > i + 1:  # End of docstring
                        new_lines.append(next_line)
                        new_lines.append(' ' * (indent_level + 4) + 'db = get_db()')
                        added_get_db = True
                    # If no docstring, add after first non-empty line
                    elif not next_line.strip().startswith('"""') and not added_get_db:
                        new_lines.append(' ' * (indent_level + 4) + 'db = get_db()')
                        new_lines.append(next_line)
                        added_get_db = True
                    else:
                        new_lines.append(next_line)
                    
                    k += 1
                
                i = k
                continue
        
        i += 1
    
    # Write back the file
    new_content = '\n'.join(new_lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    """Fix all Python files in repositories and services"""
    base_dir = Path(__file__).parent / 'app'
    
    # Fix repositories
    repo_dir = base_dir / 'db' / 'repositories'
    for py_file in repo_dir.glob('*.py'):
        if py_file.name != '__init__.py':
            try:
                fix_file(py_file)
                print(f"  ✓ Fixed {py_file.name}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    # Fix services
    services_dir = base_dir / 'services'
    for py_file in services_dir.glob('*.py'):
        if py_file.name != '__init__.py':
            try:
                # Only fix if it imports database
                with open(py_file, 'r') as f:
                    content = f.read()
                if 'from app.db.database import' in content and 'await db.' in content:
                    fix_file(py_file)
                    print(f"  ✓ Fixed {py_file.name}")
                else:
                    print(f"  - Skipped {py_file.name} (no db usage)")
            except Exception as e:
                print(f"  ✗ Error: {e}")

if __name__ == '__main__':
    main()