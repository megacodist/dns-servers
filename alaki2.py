from pathlib import Path
from typing import List, Optional, Union


class BfsNode:
    def __init__(self, data: str, parent: Optional["BfsNode"] = None):
        self.data: str = data
        self.parent: Optional["BfsNode"] = parent
        self.children: List["BfsNode"] = []

    def get_full_path(self) -> Path:
        """Traverses from this node upwards and creates the full path."""
        path_parts = []
        current_node = self
        while current_node:
            path_parts.insert(0, current_node.data)
            current_node = current_node.parent
        return Path(*path_parts)

    def add_child(self, child: "BfsNode") -> None:
        """Adds a child to this node."""
        self.children.append(child)

    def delete_child(self, child: "BfsNode") -> None:
        """Deletes a child from this node."""
        if child in self.children:
            self.children.remove(child)
        else:
            raise ValueError(f"Child {child.data} not found in children of {self.data}")

    def __repr__(self):
        return f"BfsNode(data={self.data})"


class BfsTree:
    def __init__(self, root_dir: str, filename: str):
        self.root: BfsNode = BfsNode(root_dir)
        self.filename: str = filename

    def get_leaves(self) -> List[BfsNode]:
        """Returns all leaves of the tree."""
        leaves: List[BfsNode] = []

        def _find_leaves(node: BfsNode):
            if not node.children:
                leaves.append(node)
            else:
                for child in node.children:
                    _find_leaves(child)

        _find_leaves(self.root)
        return leaves
    
    def _matched(
            self,
            text: str,
            search_for: str,
            match_case: bool = False,
            whole_match: bool = False,
            ) -> bool:
        """
        Checks if a given `text` matches the `search_for` given the
        specified criteria.

        Args:
            text (str): The text to check.
            search_for (str): The text to search for.
            match_case (bool, optional): Whether to perform a case-sensitive match. Defaults to False.
            whole_match (bool, optional): Whether to match the whole word. Defaults to False.

        Returns:
            bool: True if the text matches the search criteria, False otherwise.

        """
        text_ = text if match_case else text.lower()
        search_ = search_for if match_case else search_for.lower()
        if whole_match:
            return text_ == search_
        else:
            return text_ in search_
        

    def _searchNode(
            self,
            node: BfsNode,
            filename: str,
            match_case: bool = False,
            match_whole: bool = False,
        ) -> List[Path]:
        """
        Searches for a filename within the file system starting from a
        given node.
        """
        full_path: Path = node.get_full_path()
        found_files: List[Path] = []

        if not full_path.exists():
            return found_files

        for item in full_path.iterdir():
            if item.is_file():
                if self._matched(item.name, filename, match_case, match_whole):
                    found_files.append(item)
            elif item.is_dir():
                new_node = BfsNode(str(item.name), node)
                node.add_child(new_node)

        # Removing nodes with no children (and are not root)
        nd = node
        while nd is not self.root and not nd.children:
            nd.parent.delete_child(nd)
            nd = nd.parent

        return found_files

    def search_bfs(
        self, match_case: bool = False, match_whole: bool = False
    ) -> List[Path]:
        """Performs a breadth-first search for the filename in the file system."""
        found_files: List[Path] = []
        found_files.extend(self._searchNode(self.root, self.filename, match_case, match_whole))

        for leaf in self.get_leaves():
            found_files.extend(self._searchNode(leaf, self.filename, match_case, match_whole))
        return found_files


# Example Usage (for testing):
if __name__ == "__main__":
    # Create some dummy directories and files for testing
    root_dir = Path("./test_dir")
    root_dir.mkdir(exist_ok=True)
    (root_dir / "file1.txt").touch()
    (root_dir / "File2.txt").touch()
    (root_dir / "subdir").mkdir(exist_ok=True)
    (root_dir / "subdir" / "file3.txt").touch()
    (root_dir / "subdir" / "another_file.txt").touch()
    (root_dir / "subdir2").mkdir(exist_ok=True)

    # Test case 1: Search for "file3.txt" with case-sensitive and whole match
    tree = BfsTree(str(root_dir), "file3.txt")
    results = tree.search_bfs(match_case=True, match_whole=True)
    print(f"Test 1 (Case-sensitive, whole match): {results}")

    # Test case 2: Search for "file2.txt" with case-insensitive and whole match
    tree = BfsTree(str(root_dir), "file2.txt")
    results = tree.search_bfs(match_case=False, match_whole=True)
    print(f"Test 2 (Case-insensitive, whole match): {results}")

    # Test case 3: Search for "file" with case-insensitive and partial match
    tree = BfsTree(str(root_dir), "file")
    results = tree.search_bfs(match_case=False, match_whole=False)
    print(f"Test 3 (Case-insensitive, partial match): {results}")

    # Test case 4: Search for "File" with case-sensitive and partial match
    tree = BfsTree(str(root_dir), "File")
    results = tree.search_bfs(match_case=True, match_whole=False)
    print(f"Test 4 (Case-sensitive, partial match): {results}")

    # Clean up the dummy directories and files
    import shutil
    shutil.rmtree(root_dir)
