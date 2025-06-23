#!/usr/bin/env python3
"""
Wrapper script to ensure environment variables are set before any imports.
This prevents ONNX Runtime initialization errors in Lambda.
"""
import os
import sys

# Set all environment variables FIRST, before any imports
os.environ['ORT_LOGGING_LEVEL'] = '4'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['NUMEXPR_MAX_THREADS'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['ORT_DISABLE_ALL_LOGS'] = '1'
os.environ['ONNX_DISABLE_EXCEPTIONS'] = '1'
os.environ['ORT_DISABLE_PYTHON_PACKAGE_PATH_SEARCH'] = '1'

# Monkey patch to prevent ONNX Runtime initialization errors
# This must happen before any imports that might trigger ONNX
import importlib.util
import types

# Create a dummy onnxruntime module that does nothing
dummy_onnxruntime = types.ModuleType('onnxruntime')
dummy_onnxruntime.set_default_logger_severity = lambda x: None
dummy_onnxruntime.OnnxRuntimeException = Exception

# Pre-load the dummy module into sys.modules
sys.modules['onnxruntime'] = dummy_onnxruntime

# Now we can safely import our app
try:
    # Import uvicorn and the app
    import uvicorn
    
    # Clear the dummy module and let the real one load with proper config
    del sys.modules['onnxruntime']
    
    # Import the app which will now properly configure ONNX
    from main import app
    
    # Run the app
    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
        
except Exception as e:
    print(f"Error starting app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
