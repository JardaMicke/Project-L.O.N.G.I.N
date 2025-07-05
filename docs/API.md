# L.O.N.G.I.N. API Documentation

This document provides an overview of the L.O.N.G.I.N. API endpoints, which are served through the MCP Server.

## MCP Server

The MCP (Micro-Agent Communication Protocol) Server is the main entry point for interacting with the L.O.N.G.I.N. system. It runs as a FastAPI application and exposes the following endpoints.

### `POST /mcp`

Executes a specific tool registered on the MCP server. This is the primary endpoint for all agent and module interactions with the system's capabilities.

**Request Body:**

```json
{
  "tool_name": "string",
  "args": {
    "key": "value"
  }
}
```

-   `tool_name` (string, required): The full name of the tool to execute (e.g., `file.read`).
-   `args` (object, optional): A dictionary of arguments to pass to the tool.

**Response (Success):**

```json
{
  "success": true,
  "result": "any"
}
```

-   `success` (boolean): Always `true` for a successful execution.
-   `result` (any): The data returned by the tool. The structure of this object depends on the tool that was executed.

**Response (Error):**

If the tool is not found or an error occurs during execution, the endpoint will return an HTTP `400 Bad Request` with a JSON body describing the error.

```json
{
  "detail": "Error message describing what went wrong."
}
```

### `GET /tools`

Returns a list of all available tools currently registered on the MCP server. This is useful for discovering the system's capabilities at runtime.

**Response:**

```json
{
  "tools": [
    "file.read",
    "file.write",
    "file.list_directory"
  ]
}
```

-   `tools` (array of strings): A list of all registered tool names.

## Available Tools

The following tools are currently available via the `/mcp` endpoint.

### File Plugin (`file`)

Provides tools for basic file system operations.

#### `file.read`
Reads the entire content of a specified file.

-   **`args`**:
    -   `path` (string): The full path to the file to be read.
-   **`result`**:
    -   `content` (string): The content of the file.

#### `file.write`
Writes content to a specified file, creating the directory if it doesn't exist and overwriting the file if it already exists.

-   **`args`**:
    -   `path` (string): The full path to the file to be written.
    -   `content` (string): The content to write to the file.
-   **`result`**:
    -   `message` (string): A confirmation message.

#### `file.list_directory`
Lists the files and subdirectories within a specified directory.

-   **`args`**:
    -   `path` (string): The path to the directory to list. Defaults to the current working directory if not provided.
-   **`result`**:
    -   `files` (array of strings): A list of file names in the directory.
    -   `directories` (array of strings): A list of subdirectory names in the directory.
