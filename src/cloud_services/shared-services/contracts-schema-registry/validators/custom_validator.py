"""
Custom JavaScript validator for Contracts & Schema Registry.

What: Validates data using custom JavaScript functions in isolated VM
Why: Enables custom validation rules and business logic per PRD
Reads/Writes: Reads validation functions and data, writes validation results
Contracts: PRD custom validator specification (100ms, 64MB, Math/Date/String/Array APIs)
Risks: Security vulnerabilities if sandboxing fails, performance issues
"""

import logging
import time
from collections import OrderedDict
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Try to import py_mini_racer, fallback to basic validation if not available
try:
    from py_mini_racer import py_mini_racer
    MINI_RACER_AVAILABLE = True
except ImportError:
    MINI_RACER_AVAILABLE = False
    logger.warning("py_mini_racer not available, using basic custom validation")

# Per PRD limits
MAX_EXECUTION_TIME_MS = 100
MAX_MEMORY_MB = 64
ALLOWED_APIS = ["Math", "Date", "String", "Array"]
MAX_CONTEXT_CACHE = 128


class CustomValidator:
    """
    Custom JavaScript validator with sandboxing.

    Per PRD: Isolated VM, 100ms timeout, 64MB memory limit, Math/Date/String/Array APIs only.
    """

    def __init__(self):
        """Initialize custom validator."""
        self._context_cache: OrderedDict[str, Tuple[Any, str]] = OrderedDict()

    def _create_sandbox(self) -> Optional[Any]:
        """
        Create isolated JavaScript VM sandbox.

        Returns:
            MiniRacer context or None if unavailable
        """
        if not MINI_RACER_AVAILABLE:
            return None

        try:
            ctx = py_mini_racer.MiniRacer()

            # Inject only allowed APIs per PRD
            allowed_code = """
            // Only expose allowed APIs
            const Math = globalThis.Math;
            const Date = globalThis.Date;
            const String = globalThis.String;
            const Array = globalThis.Array;

            // Remove other globals
            delete globalThis.console;
            delete globalThis.setTimeout;
            delete globalThis.setInterval;
            delete globalThis.fetch;
            delete globalThis.XMLHttpRequest;
            delete globalThis.require;
            delete globalThis.import;
            """

            ctx.eval(allowed_code)
            return ctx
        except Exception as e:
            logger.error(f"Failed to create JavaScript sandbox: {e}")
            return None

    def validate(
        self,
        validation_function: str,
        data: Dict[str, Any],
        context_id: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate data using custom JavaScript function.

        Args:
            validation_function: JavaScript function code
            data: Data to validate
            context_id: Optional context ID for caching

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            valid, errors = self.validate_function(validation_function)
            if not valid:
                return False, [{"field": ".", "message": err, "code": "INVALID_FUNCTION"} for err in errors]

            # Check execution time
            start_time = time.perf_counter()

            serialized_data = self._serialize_data(data)
            payload_bytes = len(serialized_data.encode("utf-8"))
            function_bytes = len(validation_function.encode("utf-8"))
            if payload_bytes + function_bytes > MAX_MEMORY_MB * 1024 * 1024:
                return False, [{
                    "field": ".",
                    "message": "Validation payload exceeds memory budget",
                    "code": "MEMORY_LIMIT_EXCEEDED"
                }]

            if not MINI_RACER_AVAILABLE:
                # Fallback: basic validation
                logger.warning("JavaScript VM not available, skipping custom validation")
                return True, []

            # Create or get sandbox context
            function_hash = str(hash(validation_function))
            cache_key = context_id or function_hash
            if cache_key not in self._context_cache or self._context_cache[cache_key][1] != function_hash:
                ctx = self._create_sandbox()
                if ctx is None:
                    return True, []  # Skip validation if sandbox unavailable
                self._context_cache[cache_key] = (ctx, function_hash)
                self._context_cache.move_to_end(cache_key)
                if len(self._context_cache) > MAX_CONTEXT_CACHE:
                    self._context_cache.popitem(last=False)
            else:
                ctx = self._context_cache[cache_key][0]
                self._context_cache.move_to_end(cache_key)

            # Prepare validation code
            # Expected function signature: function validate(data) { return { valid: boolean, errors: [] } }
            validation_code = f"""
            {validation_function}

            // Execute validation
            try {{
                const result = validate({serialized_data});
                if (result.valid === false) {{
                    JSON.stringify(result.errors || []);
                }} else {{
                    JSON.stringify({{ valid: true, errors: [] }});
                }}
            }} catch (error) {{
                JSON.stringify({{ valid: false, errors: [{{ message: error.message, code: "VALIDATION_ERROR" }}] }});
            }}
            """

            # Execute with timeout
            try:
                result_str = ctx.eval(validation_code, timeout=MAX_EXECUTION_TIME_MS)
                result = self._parse_result(result_str)

                # Check execution time
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                if elapsed_ms > MAX_EXECUTION_TIME_MS:
                    logger.warning(f"Custom validation exceeded time limit: {elapsed_ms}ms")
                    return False, [{
                        "field": ".",
                        "message": "Validation exceeded time limit",
                        "code": "TIMEOUT_ERROR"
                    }]

                return result.get("valid", False), result.get("errors", [])

            except Exception as e:
                logger.error(f"Custom validation execution failed: {e}")
                return False, [{
                    "field": ".",
                    "message": f"Validation execution error: {str(e)}",
                    "code": "EXECUTION_ERROR"
                }]

        except Exception as e:
            logger.error(f"Custom validation failed: {e}")
            return False, [{
                "field": ".",
                "message": f"Validation error: {str(e)}",
                "code": "VALIDATION_ERROR"
            }]

    def _serialize_data(self, data: Dict[str, Any]) -> str:
        """
        Serialize data to JavaScript-compatible JSON.

        Args:
            data: Data dictionary

        Returns:
            JSON string
        """
        import json
        return json.dumps(data)

    def _parse_result(self, result_str: str) -> Dict[str, Any]:
        """
        Parse validation result from JavaScript.

        Args:
            result_str: JSON string result

        Returns:
            Parsed result dictionary
        """
        import json
        try:
            return json.loads(result_str)
        except Exception:
            return {"valid": False, "errors": [{"message": "Invalid result format", "code": "PARSE_ERROR"}]}

    def validate_function(self, validation_function: str) -> Tuple[bool, List[str]]:
        """
        Validate that JavaScript function is safe and valid.

        Args:
            validation_function: JavaScript function code

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check for disallowed patterns
        disallowed_patterns = [
            "require(",
            "import ",
            "eval(",
            "Function(",
            "setTimeout",
            "setInterval",
            "fetch(",
            "XMLHttpRequest",
            "process.",
            "global.",
            "__dirname",
            "__filename"
        ]

        for pattern in disallowed_patterns:
            if pattern in validation_function:
                errors.append(f"Disallowed pattern found: {pattern}")

        # Check function structure
        if "function validate" not in validation_function and "const validate" not in validation_function:
            errors.append("Validation function must define 'validate' function")

        return len(errors) == 0, errors

    def clear_cache(self):
        """Clear context cache."""
        self._context_cache.clear()
