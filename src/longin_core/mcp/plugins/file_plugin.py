import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FilePlugin:
    """
    MCP Plugin for performing basic file system operations.
    """
    def __init__(self):
        """
        Initializes the FilePlugin and registers its tools.
        """
        self.name = "file"
        self.tools = {
            "read": self.read,
            "write": self.write,
            "list_directory": self.list_directory,
        }

    async def read(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reads the content of a file.

        Args:
            args (dict): A dictionary containing the 'path' to the file.

        Returns:
            dict: A dictionary with the file 'content' or an 'error' message.
        """
        path = args.get("path")
        if not path:
            logger.warning("File read failed: 'path' argument is missing.")
            return {"success": False, "error": "Path is required"}
        
        logger.info(f"Reading file from path: {path}")
        try:
            # Note: For a high-concurrency server, consider using a library like `aiofiles`
            # to avoid blocking the event loop. For this project, sync I/O is acceptable.
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "content": content}
        except FileNotFoundError:
            logger.error(f"File not found at path: {path}")
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def write(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Writes content to a file, overwriting it if it exists.

        Args:
            args (dict): A dictionary containing the 'path' and 'content'.

        Returns:
            dict: A dictionary indicating 'success' or an 'error' message.
        """
        path = args.get("path")
        content = args.get("content")

        if not path or content is None:
            logger.warning("File write failed: 'path' or 'content' argument is missing.")
            return {"success": False, "error": "Path and content are required"}

        logger.info(f"Writing {len(content)} characters to file: {path}")
        try:
            # Ensure the directory exists before writing the file
            dir_name = os.path.dirname(path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "message": f"File written successfully to {path}"}
        except Exception as e:
            logger.error(f"Error writing to file {path}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def list_directory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lists the contents of a directory.

        Args:
            args (dict): A dictionary containing the 'path' to the directory.

        Returns:
            dict: A dictionary with 'files' and 'directories' or an 'error'.
        """
        path = args.get("path", ".")
        logger.info(f"Listing directory: {path}")
        try:
            items = os.listdir(path)
            files = [item for item in items if os.path.isfile(os.path.join(path, item))]
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
            return {"success": True, "files": files, "directories": dirs}
        except FileNotFoundError:
            logger.error(f"Directory not found: {path}")
            return {"success": False, "error": f"Directory not found: {path}"}
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
