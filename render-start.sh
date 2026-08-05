#!/bin/bash
# Render start command
echo "Starting PulsePlay Music server..."
uvicorn main:app --host 0.0.0.0 --port $PORT
