import os
from typing import Dict, Any
from engine.project_manager import load_json, save_json


class JsonProcessor:
    def __init__(self, project_path: str):
        """
        Initialize the processor with a project path.
        Automatically loads either processed.json or input.json.
        """
        self.project_path = project_path
        self.json_path = self._find_json_file()
        self.data: Dict[str, Any] = load_json(self.json_path)

    def _find_json_file(self) -> str:
        """
        Determine whether to load from processed.json or input.json.
        """
        processed = os.path.join(self.project_path, "processed.json")
        input_file = os.path.join(self.project_path, "input.json")
        return processed if os.path.exists(processed) else input_file

    def get_data(self) -> Dict[str, Any]:
        """
        Return the full loaded JSON object.
        """
        return self.data

    def set_data(self, new_data: Dict[str, Any]):
        """
        Replace the JSON with new content.
        """
        self.data = new_data
        save_json(self.data, self.json_path)
        print(f"💾 Saved: {self.json_path}")
