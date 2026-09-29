cd face-verification/packages/face-verification
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
face-verify download-models                        # online, once
face-verify download-models --zip ./buffalo_l.zip   # air-gapped alternative
