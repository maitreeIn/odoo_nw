# Running Print Server on Windows

If you are running the Odoo Print Server in Docker on Windows, it **cannot access your physical Windows printers** because the container runs Linux and expects a CUPS server (which Windows does not provide in the standard way).

To print to physical Windows printers, you must run the Print Server application **natively on Windows** (outside of Docker).

## Prerequisites

1.  **Python**: Install Python 3.x for Windows.
2.  **Dependencies**: Install the required Python packages.

## Installation Steps

1.  Open PowerShell or Command Prompt.
2.  Navigate to the `print_server` directory:
    ```powershell
    cd d:\POS\odoo_neck\print_server
    ```
3.  Install dependencies (including `pywin32` for Windows printing):
    ```powershell
    pip install -r requirements.txt
    pip install pywin32
    ```

## Configuration

1.  Edit `config.py` (optional) to set your printer names if needed.
2.  Ensure `MOCK_MODE` is `False`.

## Running the Server

Run the server using Python:

```powershell
python app.py
```

The server should start on port 5000.
You should see output like:
```
🖨️  Print Server Starting
...
🪟 Detected Windows - Using Windows Printer Handler
```

## Connecting Odoo to Windows Print Server

Since the Print Server is now running on the host (Windows) and Odoo is in Docker, Odoo needs to connect to the host machine.

1.  In Odoo, go to System Parameters.
2.  Change `sale_custom.print_server_url` to:
    *   `http://host.docker.internal:5000`
    *   OR your computer's LAN IP (e.g., `http://192.168.1.100:5000`)

Now try syncing printers again!
