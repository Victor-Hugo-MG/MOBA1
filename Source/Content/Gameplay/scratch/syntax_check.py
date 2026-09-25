import py_compile
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = 0
total = 0

for dirpath, _, filenames in os.walk(root):
    # Skip __pycache__ and scratch
    if '__pycache__' in dirpath or 'scratch' in dirpath:
        continue
    for f in sorted(filenames):
        if f.endswith('.py') and not f.startswith('__'):
            fpath = os.path.join(dirpath, f)
            total += 1
            try:
                py_compile.compile(fpath, doraise=True)
                print(f"  OK  {os.path.relpath(fpath, root)}")
            except py_compile.PyCompileError as e:
                errors += 1
                print(f"  ERR {os.path.relpath(fpath, root)}")
                print(f"      {e}")

print(f"\nScanned {total} files. Errors found: {errors}")
