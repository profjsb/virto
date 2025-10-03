"""
Tests for orchestration layer.
"""

import pytest

from src.orchestration.dag import DAG, Node


@pytest.mark.unit
def test_dag_creation():
    """Test creating a simple DAG."""

    def dummy_fn(ctx):
        return {"result": "value"}

    node = Node(id="node1", fn=dummy_fn)
    dag = DAG(nodes=[node])
    assert len(dag.nodes) == 1
    assert "node1" in dag.nodes


@pytest.mark.unit
def test_dag_single_node_execution():
    """Test DAG with single node."""

    def simple_fn(ctx):
        return {"output": "hello"}

    node = Node(id="node1", fn=simple_fn)
    dag = DAG(nodes=[node])

    result = dag.run(context={})
    assert result["node1"] == {"output": "hello"}


@pytest.mark.unit
def test_dag_execution_order():
    """Test DAG executes nodes in correct order."""
    results = []

    def make_fn(name):
        def fn(ctx):
            results.append(name)
            return {name: "done"}

        return fn

    node1 = Node(id="node1", fn=make_fn("node1"))
    node2 = Node(id="node2", fn=make_fn("node2"), depends_on=["node1"])
    node3 = Node(id="node3", fn=make_fn("node3"), depends_on=["node1"])

    dag = DAG(nodes=[node1, node2, node3])
    dag.run(context={})

    # node1 should execute first
    assert results[0] == "node1"
    # node2 and node3 can be in any order, but both after node1
    assert "node2" in results
    assert "node3" in results


@pytest.mark.unit
def test_dag_with_context():
    """Test DAG nodes receive context."""

    def use_context(ctx):
        return {"sum": ctx.get("a", 0) + ctx.get("b", 0)}

    node = Node(id="add", fn=use_context)
    dag = DAG(nodes=[node])

    result = dag.run(context={"a": 5, "b": 3})
    assert result["add"] == {"sum": 8}


@pytest.mark.unit
def test_dag_cyclic_dependency_detection():
    """Test that DAG detects cyclic dependencies."""

    def dummy_fn(ctx):
        return {"result": "value"}

    node1 = Node(id="node1", fn=dummy_fn, depends_on=["node2"])
    node2 = Node(id="node2", fn=dummy_fn, depends_on=["node1"])

    with pytest.raises(ValueError, match="cycle detected"):
        DAG(nodes=[node1, node2])
