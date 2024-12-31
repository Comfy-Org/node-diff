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

