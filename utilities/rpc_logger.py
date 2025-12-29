import json
import os
from datetime import datetime
from typing import Any, Dict

class RpcLogger:
    LOG_FILE = "logs/rpc_logs.jsonl"

    @staticmethod
    def _ensure_log_dir():
        os.makedirs(os.path.dirname(RpcLogger.LOG_FILE), exist_ok=True)

    @staticmethod
    def log_interaction(sender: str, receiver: str, data: Dict[str, Any], direction: str):
        """
        Log a JSON RPC interaction.

        Args:
            sender (str): Name of the sending agent.
            receiver (str): Name of the receiving agent.
            data (Dict[str, Any]): The JSON RPC data (request or response).
            direction (str): "send" or "receive"
        """
        RpcLogger._ensure_log_dir()
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "sender": sender,
            "receiver": receiver,
            "direction": direction,
            "data": data
        }
        with open(RpcLogger.LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")