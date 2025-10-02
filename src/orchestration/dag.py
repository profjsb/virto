from typing import Callable, Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class Node:
    id: str
    fn: Callable[[Dict[str, Any]], Dict[str, Any]]
    depends_on: List[str] = field(default_factory=list)

class DAG:
    def __init__(self, nodes: List[Node]):
        self.nodes = {n.id:
            n for n in nodes}
        # basic cycle check
        self._check_cycles()

    def _check_cycles(self):
        seen, stack = set(), set()
        def visit(nid):
            if nid in stack:
                raise ValueError("cycle detected")
            if nid in seen:
                return
            stack.add(nid)
            seen.add(nid)
            for dep in self.nodes[nid].depends_on:
                visit(dep)
            stack.remove(nid)
        for nid in list(self.nodes.keys()):
            visit(nid)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        done = set()
        while len(done) < len(self.nodes):
            progress = False
            for nid, node in self.nodes.items():
                if nid in done:
                    continue
                if all(dep in done for dep in node.depends_on):
                    out = node.fn({**context, **results})
                    results[nid] = out
                    done.add(nid)
                    progress = True
            if not progress:
                raise RuntimeError("DAG could not make progress (missing deps?)")
        return results
