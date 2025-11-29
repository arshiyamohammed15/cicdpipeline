"""
Generate OpenAPI specification from FastAPI app.
"""

"""
Generate OpenAPI specification from FastAPI app.
"""

import json
import sys
import os
import importlib.util

# Load main module directly
main_path = os.path.join(os.path.dirname(__file__), "main.py")
spec = importlib.util.spec_from_file_location("main", main_path)
main_module = importlib.util.module_from_spec(spec)
sys.modules["main"] = main_module
spec.loader.exec_module(main_module)

from fastapi.openapi.utils import get_openapi

app = main_module.app

# Generate OpenAPI schema
openapi_schema = get_openapi(
    title=app.title,
    version=app.version,
    description=app.description,
    routes=app.routes,
)

# Write to file
output_path = os.path.join(os.path.dirname(__file__), "openapi_spec.json")
with open(output_path, "w") as f:
    json.dump(openapi_schema, f, indent=2)

print(f"OpenAPI specification generated: {output_path}")

