from treelib import Tree
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_pascal
from datetime import datetime
from typing import Self, List, Set, Final, Dict, Sequence


class Process(BaseModel):
    """
    A process node in the tree structure. It uses ASIM (Advanced Security Information Model) field names.

    Field relationships in a process tree:
        grandparent.exe (PID: 100)                    # parent_process_*
                ↓
        parent.exe (PID: 200)                         # acting_process_*
                ↓
        current_process.exe (PID: 300)                # target_process_*

    For a process creation event:
    - target_process_*:  The new process being created
    - acting_process_*:  The direct parent that created this process
    - parent_process_*:  The grandparent process (parent of the acting process)

    """

    MISSING_PROCESS_ID: Final[int] = -1
    MISSING_FILE_NAME: Final[str] = "MISSING"
    MISSING_CREATION_TIME: Final[datetime] = datetime(1970, 1, 1)

    model_config = ConfigDict(
        # Allow extra fields to be passed without raising validation errors
        extra="ignore",
        # Enable automatic conversion from PascalCase to snake_case
        # Example: 'TargetProcessId' -> 'target_process_id'
        alias_generator=to_pascal,
        # Allow both alias and direct field names during model creation
        # Example: Process(target_process_id=123) or Process(TargetProcessId=123)
        populate_by_name=True,
    )

    # Process being created
    target_process_id: int
    target_process_filename: str
    target_process_creation_time: datetime

    # Direct parent process
    acting_process_id: int = MISSING_PROCESS_ID
    acting_process_filename: str = MISSING_FILE_NAME
    acting_process_creation_time: datetime = MISSING_CREATION_TIME

    # TODO: A special case occurs when you reboot the machine. then you get parent_process_pid = 0
    # with some None/null values for the filename and an invalid datetime!

    # Grandparent process
    parent_process_id: int = MISSING_PROCESS_ID
    parent_process_filename: str = MISSING_FILE_NAME
    parent_process_creation_time: datetime = MISSING_CREATION_TIME

    def identifier(self) -> str:
        return f"{self.target_process_id}|{self.target_process_creation_time}"

    def parent_identifier(self) -> str:
        if self.acting_process_id == Process.MISSING_PROCESS_ID:
            return "<root>"

        return f"{self.acting_process_id}|{self.acting_process_creation_time}"

    def tag(self) -> str:
        return f"{self.target_process_filename} ({self.target_process_id})"


class ProcessTree:
    """A hierarchical representation of process relationships using a tree data structure.

    This class manages process relationships where each node represents a process with its
    metadata (PID, filename, creation time, etc.). It automatically handles missing parent
    processes by creating placeholder nodes to maintain the correct hierarchy.

    Features:
    - Builds process trees from a list of Process objects
    - Handles missing parent/grandparent processes automatically
    - Supports various export formats (dependentree, observable)
    - Provides methods for tree traversal and process lookup

    Example tree structure:
    ```plain
        <root>
        ├── MsSense.exe (3436)
        │   ├── SenseIR.exe (2224)
        │   │   └── powershell.exe (5416)
        │   │       ├── conhost.exe (4440)
        │   │       └── csc.exe (728)
        │   │           └── cvtres.exe (5000)
        ...
    ```
    """

    def __init__(self, processes: List | None = None):
        self.tree: Tree = Tree()
        self.root = self.tree.create_node(tag="<root>", identifier="<root>", data=None)

        if processes:
            self.build_tree(processes)

    def build_tree(self, processes: List) -> Self:
        for process in processes:
            _process = Process.model_validate(process)
            self.insert_process(_process)

        return self

    def insert_or_update(self, process: Process) -> None:
        """ """

        node = self.tree.get_node(process.identifier())
        if not node:
            self.tree.create_node(
                tag=process.tag(),
                identifier=process.identifier(),
                parent=process.parent_identifier(),
                data=process,
            )
        else:
            existing_process = node.data

            if process.acting_process_id != Process.MISSING_PROCESS_ID:
                self.tree.update_node(
                    process.identifier(),
                    tag=process.tag(),
                    data=process,
                )

                if existing_process.parent_identifier() != process.parent_identifier():
                    self.tree.move_node(
                        process.identifier(), process.parent_identifier()
                    )

    def insert_process(self, process: Process) -> None:
        """
        Insert a process into the tree, creating any missing ancestor nodes.
        """

        # this is the grand parent of the process that is created
        parent_process = Process(
            target_process_id=process.parent_process_id,
            target_process_filename=process.parent_process_filename,
            target_process_creation_time=process.parent_process_creation_time,
        )

        # this is the parent of the process that is created
        acting_process = Process(
            target_process_id=process.acting_process_id,
            target_process_filename=process.acting_process_filename,
            target_process_creation_time=process.acting_process_creation_time,
            acting_process_id=process.parent_process_id,
            acting_process_filename=process.parent_process_filename,
            acting_process_creation_time=process.parent_process_creation_time,
        )

        self.insert_or_update(parent_process)
        self.insert_or_update(acting_process)
        self.insert_or_update(process)

    def get_all_pids(self) -> Set[int]:
        """
        Returns the set of all process ids in the tree.
        """
        return set(
            (
                node.data.target_process_id
                for node in self.tree.all_nodes_itr()
                if node.data
            )
        )

    def create_dependentree_format(self) -> List[Dict[str, Sequence[str]]]:
        """
        This takes the tree and generates the format expected by https://github.com/square/dependentree.
        """
        tree = []
        for node in self.tree.all_nodes():
            if node.data is None:
                data = {"_name": "<root>", "_deps": []}
            else:
                process = node.data
                data = {
                    "_name": process.identifier(),
                    "_deps": [process.parent_identifier()],
                    "ProcessName": process.target_process_filename,
                    "ProcessId": process.target_process_id,
                    "ProcessCreationTime": process.target_process_creation_time,
                }

            tree.append(data)

        return tree

    def display(self) -> str:
        """
        Returns a string representation of the process tree.

        The output format is a hierarchical tree structure where each line represents
        a process with its file name and process ID, indented to show parent-child
        relationships.

        Returns:
            str: A formatted string showing the process hierarchy.
        """
        return str(self.tree)
