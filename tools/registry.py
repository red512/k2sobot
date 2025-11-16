"""
Tool registry for automatic tool discovery and registration
"""
import os
import importlib.util
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry for automatically discovering and managing tools"""

    def __init__(self):
        self._tools = []
        self._function_map = {}

    def discover_tools(self, tools_dir=None):
        """Automatically discover all tools from the tools directory"""
        if tools_dir is None:
            tools_dir = Path(__file__).parent

        tools_dir = Path(tools_dir)
        self._tools.clear()
        self._function_map.clear()

        # Find all Python files in tools directory (except __init__.py and registry.py)
        tool_files = [
            f for f in tools_dir.glob("*.py")
            if f.name not in ["__init__.py", "registry.py"]
        ]

        for tool_file in tool_files:
            self._load_tools_from_file(tool_file)

        logger.info(f"✅ Discovered {len(self._tools)} tools from {len(tool_files)} modules")
        return self._tools

    def _load_tools_from_file(self, file_path):
        """Load all tools from a specific file"""
        try:
            # Import the module
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all callable functions that don't start with _
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    attr = getattr(module, attr_name)
                    if callable(attr) and hasattr(attr, '__doc__'):
                        # Check if it has the required tool metadata
                        if self._is_valid_tool(attr):
                            self._tools.append(attr)
                            self._function_map[attr_name] = attr
                            logger.debug(f"Registered tool: {attr_name}")

        except Exception as e:
            logger.warning(f"Failed to load tools from {file_path}: {e}")

    def _is_valid_tool(self, func):
        """Check if a function is a valid tool (has docstring and is callable)"""
        import types
        return (
            callable(func) and
            isinstance(func, types.FunctionType) and  # Must be a function, not class/module
            func.__doc__ is not None and
            func.__doc__.strip() != "" and
            func.__module__ is not None and  # Must have a module (not built-in)
            not func.__name__.startswith('_')  # Not private
        )

    def get_tools(self):
        """Get all discovered tools"""
        return self._tools

    def get_function_map(self):
        """Get the function name -> function mapping"""
        return self._function_map

    def execute_tool(self, function_name, **kwargs):
        """Execute a tool by name"""
        if function_name not in self._function_map:
            return {"error": f"Unknown function: {function_name}"}

        try:
            func = self._function_map[function_name]
            return func(**kwargs) if kwargs else func()
        except Exception as e:
            logger.error(f"Error executing {function_name}: {e}")
            return {"error": str(e)}

# Global registry instance
_registry = ToolRegistry()

def get_tool_registry():
    """Get the global tool registry instance"""
    return _registry

def discover_and_get_tools():
    """Convenience function to discover tools and return them"""
    registry = get_tool_registry()
    return registry.discover_tools()

def get_function_map():
    """Convenience function to get the function mapping"""
    registry = get_tool_registry()
    return registry.get_function_map()

def execute_tool(function_name, **kwargs):
    """Convenience function to execute a tool"""
    registry = get_tool_registry()
    return registry.execute_tool(function_name, **kwargs)