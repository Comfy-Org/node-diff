from typing import Type, Dict, Any, Set, Tuple
import sys
import importlib.util
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import os

class BreakingChangeType(Enum):
    RETURN_TYPES_CHANGED = "Return types changed"
    RETURN_TYPES_REORDERED = "Return types reordered"
    INPUT_REMOVED = "Required input removed"
    INPUT_TYPE_CHANGED = "Input type changed"
    NODE_REMOVED = "Node removed"
    FUNCTION_CHANGED = "Entry point function changed"

@dataclass
class BreakingChange:
    node_name: str
    change_type: BreakingChangeType
    details: str
    base_value: Any = None
    pr_value: Any = None

def load_node_mappings(repo_path: str) -> Dict[str, Type]:
    """
    Load NODE_CLASS_MAPPINGS from a repository's __init__.py
    """
    init_path = os.path.join(repo_path, "__init__.py")
    
    if not os.path.exists(init_path):
        raise FileNotFoundError(f"Could not find __init__.py in {repo_path}")
    
    # Add the repo path to system path temporarily
    sys.path.insert(0, os.path.dirname(repo_path))
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("module", init_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load module from {init_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get NODE_CLASS_MAPPINGS
        mappings = getattr(module, "NODE_CLASS_MAPPINGS", {})
        if not mappings:
            raise AttributeError("NODE_CLASS_MAPPINGS not found in __init__.py")
            
        return mappings
    
    finally:
        # Remove the temporary path
        sys.path.pop(0)


def get_node_classes(module) -> Dict[str, Type]:
    """Extract node classes from module using NODE_CLASS_MAPPINGS."""
    return getattr(module, "NODE_CLASS_MAPPINGS", {})

def compare_return_types(node_name: str, base_class: Type, pr_class: Type) -> list[BreakingChange]:
    """Compare RETURN_TYPES between base and PR versions of a node."""
    changes = []
    base_types = getattr(base_class, "RETURN_TYPES", tuple())
    pr_types = getattr(pr_class, "RETURN_TYPES", tuple())

    if len(base_types) != len(pr_types):
        changes.append(BreakingChange(
            node_name=node_name,
            change_type=BreakingChangeType.RETURN_TYPES_CHANGED,
            details=f"Number of return types changed from {len(base_types)} to {len(pr_types)}",
            base_value=base_types,
            pr_value=pr_types
        ))
        return changes

    # Check for type changes and reordering
    base_types_set = set(base_types)
    pr_types_set = set(pr_types)
    
    if base_types_set != pr_types_set:
        changes.append(BreakingChange(
            node_name=node_name,
            change_type=BreakingChangeType.RETURN_TYPES_CHANGED,
            details="Return types changed",
            base_value=base_types,
            pr_value=pr_types
        ))
    elif base_types != pr_types:
        changes.append(BreakingChange(
            node_name=node_name,
            change_type=BreakingChangeType.RETURN_TYPES_REORDERED,
            details="Return types were reordered",
            base_value=base_types,
            pr_value=pr_types
        ))

    return changes

def compare_input_types(node_name: str, base_class: Type, pr_class: Type) -> list[BreakingChange]:
    """Compare INPUT_TYPES between base and PR versions of a node."""
    changes = []
    
    base_inputs = base_class.INPUT_TYPES().get("required", {})
    pr_inputs = pr_class.INPUT_TYPES().get("required", {})

    # Check for removed inputs
    for input_name, input_config in base_inputs.items():
        if input_name not in pr_inputs:
            changes.append(BreakingChange(
                node_name=node_name,
                change_type=BreakingChangeType.INPUT_REMOVED,
                details=f"Required input '{input_name}' was removed",
                base_value=input_config,
                pr_value=None
            ))
            continue

        # Check input type changes
        if pr_inputs[input_name][0] != input_config[0]:
            changes.append(BreakingChange(
                node_name=node_name,
                change_type=BreakingChangeType.INPUT_TYPE_CHANGED,
                details=f"Input type changed for '{input_name}'",
                base_value=input_config[0],
                pr_value=pr_inputs[input_name][0]
            ))

    return changes

def compare_function(node_name: str, base_class: Type, pr_class: Type) -> list[BreakingChange]:
    """Compare FUNCTION attribute between base and PR versions of a node."""
    changes = []
    
    base_function = getattr(base_class, "FUNCTION", None)
    pr_function = getattr(pr_class, "FUNCTION", None)
    
    if base_function != pr_function:
        changes.append(BreakingChange(
            node_name=node_name,
            change_type=BreakingChangeType.FUNCTION_CHANGED,
            details="Entry point function changed",
            base_value=base_function,
            pr_value=pr_function
        ))
    
    return changes

def compare_nodes(base_nodes: Dict[str, Type], pr_nodes: Dict[str, Type]) -> list[BreakingChange]:
    """Compare two versions of nodes for breaking changes."""
    changes = []
    
    # Check for removed nodes
    for node_name in base_nodes:
        if node_name not in pr_nodes:
            changes.append(BreakingChange(
                node_name=node_name,
                change_type=BreakingChangeType.NODE_REMOVED,
                details="Node was removed",
            ))
            continue
            
        base_class = base_nodes[node_name]
        pr_class = pr_nodes[node_name]
        
        changes.extend(compare_return_types(node_name, base_class, pr_class))
        changes.extend(compare_input_types(node_name, base_class, pr_class))
        changes.extend(compare_function(node_name, base_class, pr_class))
    
    return changes

def format_breaking_changes(changes: list[BreakingChange]) -> str:
    """Format breaking changes into a clear error message."""
    if not changes:
        return "✅ No breaking changes detected"
        
    output = ["❌ Breaking changes detected:\n"]
    
    # Group changes by node
    changes_by_node = {}
    for change in changes:
        if change.node_name not in changes_by_node:
            changes_by_node[change.node_name] = []
        changes_by_node[change.node_name].append(change)
    
    # Format each node's changes
    for node_name, node_changes in changes_by_node.items():
        output.append(f"Node: {node_name}")
        for change in node_changes:
            output.append(f"  • {change.change_type.value}: {change.details}")
            if change.base_value is not None:
                output.append(f"    - Base: {change.base_value}")
            if change.pr_value is not None:
                output.append(f"    - PR: {change.pr_value}")
        output.append("")
    
    return "\n".join(output)

def main():
    if len(sys.argv) != 3:
        print("Usage: validate_nodes.py <base_repo_path> <pr_repo_path>")
        sys.exit(1)
        
    base_path = sys.argv[1]
    pr_path = sys.argv[2]
    
    try:
        base_nodes = load_node_mappings(base_path)
        pr_nodes = load_node_mappings(pr_path)
    except Exception as e:
        print(f"❌ Error loading nodes: {str(e)}")
        sys.exit(1)
    
    breaking_changes = compare_nodes(base_nodes, pr_nodes)
    print(format_breaking_changes(breaking_changes))
    
    if breaking_changes:
        sys.exit(1)

if __name__ == "__main__":
    main()
