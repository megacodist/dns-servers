from pathlib import Path
from collections import deque

def searchBfs(
        dir_: str,
        filename: str,
        match_case: bool = False,
        match_whole: bool = False,
        ) -> None:
    """
    Performs breadth-first search for filename in a
    subfolder of dir with options for match case and match whole word.
    
    Parameters:
        dir_: file system path to a folder
        filename: name and extension of a file to be found
        match_case: whether the search should be case-sensitive
        match_whole: whether the search should match the whole word
    """
    # Initializing the queue...
    q = deque[Path]()
    q.append(Path(dir_))  # Push the initial directory into the queue
    #
    while q:  # While the queue is not empty
        subdir = q.popleft()  # Pop from the front of the queue
        # Iterate over all items in the subdir
        for item in subdir.iterdir():
            if item.is_file():  # Check if the item is a file
                itemName = item.name if match_case else item.name.lower()
                searchName = filename if match_case else filename.lower()
                found = itemName == searchName if match_whole else \
                    searchName in itemName
                if found:
                    print(f"Found: {item.resolve()}")  # Report the full path of the item
            elif item.is_dir():  # Check if the item is a folder
                q.append(item)  # Push the full path of the folder into the queue


if __name__ == "__main__":
    pass
