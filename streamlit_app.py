"""
Root Streamlit entrypoint.

Why this exists:
- Streamlit executes the provided script with that script's directory on sys.path.
- If you run `streamlit run urdb_viewer/main.py`, sys.path points at `urdb_viewer/`,
  which breaks absolute imports like `import urdb_viewer...`.
- Running this file from the repo root keeps the project root on sys.path, so the
  `urdb_viewer` package imports correctly without any sys.path hacks.
"""

from urdb_viewer.main import main

if __name__ == "__main__":
    main()
