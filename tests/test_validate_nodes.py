import pytest
from src.validate_nodes import compare_return_types, BreakingChangeType

class BaseNode:
    RETURN_TYPES = ("STRING", "INT", "FLOAT")

class PRNode:
    RETURN_TYPES = ("STRING", "INT", "FLOAT")

class ReorderedNode:
    RETURN_TYPES = ("INT", "STRING", "FLOAT")

class IncompatibleNode:
    RETURN_TYPES = ("STRING", "BOOL", "FLOAT")

class AddTypeNode:
    RETURN_TYPES = ("STRING", "INT", "FLOAT", "BOOL")

class RemoveTypeNode:
    RETURN_TYPES = ("STRING", "INT")

class NoReturnTypesNode:
    pass

def test_compare_return_types_no_changes():
    changes = compare_return_types("TestNode", BaseNode, PRNode)
    assert len(changes) == 0


def test_compare_return_types_add_type():
    changes = compare_return_types("TestNode", BaseNode, AddTypeNode)
    assert len(changes) == 0

def test_compare_return_types_remove_type():
    changes = compare_return_types("TestNode", BaseNode, RemoveTypeNode)
    assert len(changes) == 1
    assert changes[0].change_type == BreakingChangeType.RETURN_TYPES_CHANGED
    assert changes[0].base_value == ("STRING", "INT", "FLOAT")
    assert changes[0].pr_value == ("STRING", "INT")

def test_compare_return_types_reordered():
    changes = compare_return_types("TestNode", BaseNode, ReorderedNode)
    assert len(changes) == 1
    assert changes[0].change_type == BreakingChangeType.RETURN_TYPES_CHANGED
    assert changes[0].base_value == ("STRING", "INT", "FLOAT")
    assert changes[0].pr_value == ("INT", "STRING", "FLOAT")

def test_compare_return_types_incompatible():
    changes = compare_return_types("TestNode", BaseNode, IncompatibleNode)
    assert len(changes) == 1
    assert changes[0].change_type == BreakingChangeType.RETURN_TYPES_CHANGED
    assert changes[0].base_value == ("STRING", "INT", "FLOAT")
    assert changes[0].pr_value == ("STRING", "BOOL", "FLOAT")

def test_compare_return_types_missing():
    changes = compare_return_types("TestNode", BaseNode, NoReturnTypesNode)
    assert len(changes) == 1
    assert changes[0].change_type == BreakingChangeType.RETURN_TYPES_CHANGED
    assert changes[0].base_value == ("STRING", "INT", "FLOAT")
    assert changes[0].pr_value == tuple()


def test_compare_function():
    from src.validate_nodes import compare_function, BreakingChangeType

    class BaseNode:
        FUNCTION = "process"

    class PRNode:
        FUNCTION = "process"

    class ChangedNode:
        FUNCTION = "different_process"

    class NoFunctionNode:
        pass

    # Test 1: No changes
    changes = compare_function("TestNode", BaseNode, PRNode)
    assert len(changes) == 0

    # Test 2: Function changed
    changes = compare_function("TestNode", BaseNode, ChangedNode)
    assert len(changes) == 1
    assert changes[0].change_type == BreakingChangeType.FUNCTION_CHANGED
    assert changes[0].base_value == "process"
    assert changes[0].pr_value == "different_process"

    # Test 3: Function removed
    changes = compare_function("TestNode", BaseNode, NoFunctionNode)
    assert len(changes) == 1
    assert changes[0].change_type == BreakingChangeType.FUNCTION_CHANGED
    assert changes[0].base_value == "process"
    assert changes[0].pr_value is None

    # Test 4: Function added (not a breaking change if base had none)
    changes = compare_function("TestNode", NoFunctionNode, BaseNode)
    assert len(changes) == 1
    assert changes[0].change_type == BreakingChangeType.FUNCTION_CHANGED
    assert changes[0].base_value is None
    assert changes[0].pr_value == "process"
