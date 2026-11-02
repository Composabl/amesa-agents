#!/usr/bin/env python3
# Copyright (C) Amesa, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import argparse
import os
import asyncio
from typing import Optional

from amesa_core.networking.sim.server import make_from_sim_path


async def _run(
    path: Optional[str] = "./",
    host: Optional[str] = "0.0.0.0",
    port: Optional[int] = 1337,
    protocol: Optional[str] = "grpc",
    config: Optional[dict] = {},
):
    path_abs = os.path.abspath(path)

    print(f"Running sim from path: {path_abs}")
    print(f"Params: {path}, {host}, {port}, {protocol}, {config}")

    server = make_from_sim_path(path, host, port, config=config, protocol=protocol)
    print(f"Running on {host}:{port}")

    try:
        await server.start()
    except KeyboardInterrupt:
        print("KeyboardInterrupt, Gracefully stopping the server")
    except Exception as e:
        print(f"Unknown error: {e}, Gracefully stopping the server")
    finally:
        print("Stopping the server")
        if server is not None:
            await server.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default="./")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=1337)
    parser.add_argument("--protocol", type=str, default="grpc")
    parser.add_argument("--config", type=str, default="{}")
    args = parser.parse_args()

    config_parsed = eval(args.config)

    asyncio.run(_run(args.path, args.host, args.port, args.protocol, config_parsed))