import asyncio
import os
import socket
import subprocess
import sys

import httpx
from mcp import Client

from drift_gym.client import ToolClient


async def test_streamable_http_round_trip(database):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "drift_gym.server",
            "--db",
            str(database),
            "--http",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        async with asyncio.timeout(60), httpx.AsyncClient() as http:
            while True:
                assert process.poll() is None, "HTTP server exited before readiness"
                try:
                    await http.get(url)
                    break
                except httpx.ConnectError:
                    await asyncio.sleep(0.1)
        async with Client(url, cache=None) as connection:
            assert connection.protocol_version == "2026-07-28"
            client = ToolClient(connection, [])
            assert len(await client.schemas()) == 7
            assert (await client.call("get_refund_policy"))["version"] == 3
    finally:
        process.terminate()
        await asyncio.to_thread(process.wait, timeout=10)
