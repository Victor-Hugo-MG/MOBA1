import sys, os

# Get the absolute path of this Gameplay directory
GAMEPLAY_ROOT = os.path.dirname(__file__)

# Add subdirectories to sys.path to allow clean "from Core import ..." style imports
SUBDIRS = ["Core", "Data", "AI", "UI"]
for sub in SUBDIRS:
	path = os.path.join(GAMEPLAY_ROOT, sub)
	if path not in sys.path:
		sys.path.append(path)

print(f"[MOBA] Framework Initialized. Paths: {SUBDIRS}")
