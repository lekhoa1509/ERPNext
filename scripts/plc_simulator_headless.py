#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_SIGNALS_PATH = Path(__file__).resolve().parents[1] / ".." / "Simulator" / "TQG.PlcEmulator.CrossPlatform" / "signals.json"
DEFAULT_PORT = 5021
DEFAULT_AUTH_KEY = "868686"
DEFAULT_BARCODE = "ERPDEMO001"


@dataclass
class PendingCommand:
    command_type: str
    auto_barcode_sent: bool = False
    active: bool = False


class SignalMapping:
    def __init__(self, devices: Dict[str, Any]):
        self.devices = devices

    @classmethod
    def load(cls, file_path: Path) -> "SignalMapping":
        payload = json.loads(file_path.read_text())
        return cls({device["deviceId"]: device for device in payload})

    def get_all_slot_keys(self) -> List[str]:
        keys = []
        for device in self.devices.values():
            for slot in device.get("slots", []):
                keys.append(f"{device['deviceId']}:Slot{slot['slotId']}")
        return keys

    def get_slot(self, slot_key: str) -> Optional[Dict[str, Any]]:
        device_id, slot_id = self.parse_slot_key(slot_key)
        device = self.devices.get(device_id)
        if not device:
            return None

        for slot in device.get("slots", []):
            if slot.get("slotId") == slot_id:
                return slot

        return None

    def get_signal_info(self, slot_key: str, address: str) -> Optional[Dict[str, Any]]:
        slot = self.get_slot(slot_key)
        if not slot:
            return None

        for bucket in ("controlCommands", "statusFeedback", "positionData", "barcodeData"):
            signals = slot.get(bucket, {})
            if address in signals:
                return signals[address]

        return None

    def find_signal_address_by_name(self, slot_key: str, friendly_name: str) -> Optional[str]:
        slot = self.get_slot(slot_key)
        if not slot:
            return None

        for bucket in ("controlCommands", "statusFeedback", "positionData", "barcodeData"):
            for address, signal in slot.get(bucket, {}).items():
                if str(signal.get("name", "")).lower() == friendly_name.lower():
                    return address

        return None

    def get_signal_addresses(self, slot_key: str) -> List[str]:
        slot = self.get_slot(slot_key)
        if not slot:
            return []

        addresses: List[str] = []
        for bucket in ("controlCommands", "statusFeedback", "positionData", "barcodeData"):
            addresses.extend(slot.get(bucket, {}).keys())
        return addresses

    @staticmethod
    def default_value(signal_type: str) -> Any:
        normalized = (signal_type or "").lower()
        if normalized == "bool":
            return False
        if normalized in {"int", "byte", "word", "dword", "real"}:
            return 0
        return ""

    @staticmethod
    def barcode_default_value() -> str:
        return "0"

    @staticmethod
    def parse_slot_key(slot_key: str) -> Tuple[str, int]:
        device_id, slot_part = slot_key.split(":Slot")
        return device_id, int(slot_part)


class HeadlessPlcSimulator:
    def __init__(self, mapping: SignalMapping, auth_key: str, default_barcode: str, auto_complete_delay: float):
        self.mapping = mapping
        self.auth_key = auth_key
        self.default_barcode = default_barcode
        self.auto_complete_delay = auto_complete_delay
        self.slot_registry: Dict[str, Dict[str, Any]] = {}
        self.pending_commands: Dict[str, Optional[PendingCommand]] = {}
        self.authenticated_by_slot: Dict[str, bool] = {}
        self.command_tasks: Dict[str, asyncio.Task] = {}
        self.slot0_key: Optional[str] = None
        self.slot1_key: Optional[str] = None
        self.slot2_key: Optional[str] = None
        self.initialize_slots()

    def initialize_slots(self) -> None:
        for slot_key in self.mapping.get_all_slot_keys():
            self.slot_registry[slot_key] = {}
            self.pending_commands[slot_key] = None
            self.authenticated_by_slot[slot_key] = False

            _, slot_id = self.mapping.parse_slot_key(slot_key)
            if slot_id == 0:
                self.slot0_key = slot_key
            elif slot_id == 1:
                self.slot1_key = slot_key
            elif slot_id == 2:
                self.slot2_key = slot_key

            for address in self.mapping.get_signal_addresses(slot_key):
                info = self.mapping.get_signal_info(slot_key, address) or {}
                name = str(info.get("name", ""))
                if name.startswith("BarcodeChar"):
                    self.slot_registry[slot_key][address] = self.mapping.barcode_default_value()
                else:
                    self.slot_registry[slot_key][address] = self.mapping.default_value(info.get("type", ""))

        for slot_key in (self.slot1_key, self.slot2_key):
            if slot_key:
                self.write_signal_by_name(slot_key, "DeviceReady", True)
                self.write_signal_by_name(slot_key, "SoftwareConnected", False)
                self.write_signal_by_name(slot_key, "CommandFailed", False)
                self.write_signal_by_name(slot_key, "ErrorAlarm", False)
                self.write_signal_by_name(slot_key, "ErrorCode", 0)

        if self.slot0_key:
            self.write_signal_by_name(self.slot0_key, "SoftwareConnected", False)
            self.write_signal_by_name(self.slot0_key, "AuthResult", 0)

    def resolve_slot_key(self, identifier: str, signal: str) -> Optional[Tuple[str, str]]:
        if ":Slot" in identifier:
            return identifier, signal

        if signal.upper().startswith("DB"):
            db_number = self._parse_db_number(signal)
            if db_number is not None:
                for slot_key in self.mapping.get_all_slot_keys():
                    slot = self.mapping.get_slot(slot_key)
                    if slot and int(slot.get("dbNumber", 0)) == db_number and slot_key.startswith(f"{identifier}:Slot"):
                        return slot_key, signal

        for slot_key in self.mapping.get_all_slot_keys():
            if not slot_key.startswith(f"{identifier}:Slot"):
                continue
            store = self.slot_registry.get(slot_key, {})
            if signal in store:
                return slot_key, signal
            address = self.mapping.find_signal_address_by_name(slot_key, signal)
            if address and address in store:
                return slot_key, address

        return None

    @staticmethod
    def _parse_db_number(signal: str) -> Optional[int]:
        if not signal.upper().startswith("DB"):
            return None

        try:
            return int(signal[2:].split(".", 1)[0])
        except (TypeError, ValueError, IndexError):
            return None

    def format_value(self, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return ""
        return str(value)

    def parse_value(self, signal_type: str, value: str) -> Any:
        normalized_type = (signal_type or "").lower()
        if normalized_type == "bool":
            if value.lower() in {"true", "1"}:
                return True
            if value.lower() in {"false", "0"}:
                return False
        if normalized_type in {"int", "byte", "word", "dword"}:
            try:
                return int(value)
            except ValueError:
                return value
        return value

    def write_signal_direct(self, slot_key: str, address: str, value: Any) -> None:
        if slot_key not in self.slot_registry:
            return
        if address not in self.slot_registry[slot_key]:
            return
        self.slot_registry[slot_key][address] = value

    def write_signal_by_name(self, slot_key: str, signal_name: str, value: Any) -> None:
        address = self.mapping.find_signal_address_by_name(slot_key, signal_name)
        if address:
            self.write_signal_direct(slot_key, address, value)

    def read_signal(self, slot_key: str, signal: str) -> Optional[Any]:
        store = self.slot_registry.get(slot_key, {})
        if signal in store:
            return store[signal]
        address = self.mapping.find_signal_address_by_name(slot_key, signal)
        if address:
            return store.get(address)
        return None

    async def process_command(self, line: str) -> str:
        if not line:
            return "ERR Empty"

        parts = line.split(" ")
        command = parts[0].upper()
        if command == "PING":
            return "PONG"
        if command == "READ":
            if len(parts) < 3:
                return "ERR Usage: READ <slotKey> <signal>"
            return self.handle_read(parts[1], parts[2])
        if command == "WRITE":
            if len(parts) < 4:
                return "ERR Usage: WRITE <slotKey> <signal> <value>"
            return await self.handle_write(parts[1], parts[2], " ".join(parts[3:]))
        if command == "LIST":
            if len(parts) < 2:
                return "ERR Usage: LIST <slotKey>"
            return self.handle_list(parts[1])
        return "ERR UnknownCommand"

    def handle_read(self, identifier: str, signal: str) -> str:
        resolved = self.resolve_slot_key(identifier, signal)
        if not resolved:
            return "ERR SlotNotFound"
        slot_key, address = resolved
        value = self.read_signal(slot_key, address)
        if value is None:
            return "ERR SignalNotFound"
        return f"OK {self.format_value(value)}"

    async def handle_write(self, identifier: str, signal: str, value: str) -> str:
        resolved = self.resolve_slot_key(identifier, signal)
        if not resolved:
            return "ERR SlotNotFound"

        slot_key, address = resolved
        info = self.mapping.get_signal_info(slot_key, address)
        signal_name = str((info or {}).get("name", signal))
        signal_type = str((info or {}).get("type", ""))
        parsed_value = self.parse_value(signal_type, value)
        self.write_signal_direct(slot_key, address, parsed_value)

        await self._handle_side_effects(slot_key, signal_name, parsed_value)
        return "OK"

    def handle_list(self, identifier: str) -> str:
        if ":Slot" not in identifier:
            lines: List[str] = []
            for slot_key in self.mapping.get_all_slot_keys():
                if not slot_key.startswith(f"{identifier}:Slot"):
                    continue
                slot = self.mapping.get_slot(slot_key) or {}
                lines.append(f"--- {slot_key} (DB{slot.get('dbNumber')}) ---")
                for address, value in sorted(self.slot_registry.get(slot_key, {}).items()):
                    lines.append(f"{address}={self.format_value(value)}")
            return "\n".join(lines) if lines else "ERR DeviceNotFound"

        if identifier not in self.slot_registry:
            return "ERR SlotNotFound"

        return "\n".join(
            f"{address}={self.format_value(value)}"
            for address, value in sorted(self.slot_registry[identifier].items())
        )

    async def _handle_side_effects(self, slot_key: str, signal_name: str, value: Any) -> None:
        if signal_name == "LoginTrigger" and value is True:
            self._process_authentication(slot_key)
            return

        if signal_name == "ConnectWmsTrigger" and value is True:
            self._process_connect_wms(slot_key)
            return

        if signal_name == "Mode1ShuttleTrigger" and value is True:
            self._set_mode_status(slot_key, mode=1)
            return

        if signal_name == "Mode2ShuttleTrigger" and value is True:
            self._set_mode_status(slot_key, mode=2)
            return

        if signal_name == "LogoutTrigger" and value is True:
            self._process_logout(slot_key)
            return

        if signal_name in {"InboundTrigger", "OutboundTrigger", "TransferTrigger", "PalletCheckTrigger"} and value is True:
            self.pending_commands[slot_key] = PendingCommand(command_type=signal_name.replace("Trigger", ""))
            return

        if signal_name == "StartProcess" and value is True:
            await self._start_pending_command(slot_key)
            return

        if signal_name == "BarcodeValid" and value is True:
            await self._complete_inbound(slot_key, valid=True)
            return

        if signal_name == "BarcodeInvalid" and value is True:
            self._reset_barcode(slot_key)
            pending = self.pending_commands.get(slot_key)
            if pending:
                pending.auto_barcode_sent = False
            return

    def _process_authentication(self, slot_key: str) -> None:
        digits = []
        for index in range(1, 7):
            value = self.read_signal(slot_key, f"KeyInput{index}")
            digit = "0"
            if isinstance(value, int):
                digit = str(abs(value) % 10)
            elif isinstance(value, str) and value:
                digit = value[0]
            digits.append(digit)

        received_key = "".join(digits)
        success = received_key == self.auth_key
        self.authenticated_by_slot[slot_key] = success
        self.write_signal_by_name(slot_key, "AuthResult", 4 if success else 1)
        self.write_signal_by_name(slot_key, "LoginTrigger", False)

    def _process_connect_wms(self, slot_key: str) -> None:
        connected = self.authenticated_by_slot.get(slot_key, False)
        for target in (self.slot0_key, self.slot1_key, self.slot2_key):
            if target:
                self.write_signal_by_name(target, "SoftwareConnected", connected)
        self.write_signal_by_name(slot_key, "ConnectWmsTrigger", False)

    def _set_mode_status(self, slot_key: str, mode: int) -> None:
        self.write_signal_by_name(slot_key, "Mode1ShuttleSts", mode == 1)
        self.write_signal_by_name(slot_key, "Mode2ShuttleSts", mode == 2)
        self.write_signal_by_name(slot_key, "PriorityModeSts", False)
        self.write_signal_by_name(slot_key, f"Mode{mode}ShuttleTrigger", False)

    def _process_logout(self, slot_key: str) -> None:
        self.authenticated_by_slot[slot_key] = False
        for target in (self.slot0_key, self.slot1_key, self.slot2_key):
            if target:
                self.write_signal_by_name(target, "SoftwareConnected", False)
        self.write_signal_by_name(slot_key, "Mode1ShuttleSts", False)
        self.write_signal_by_name(slot_key, "Mode2ShuttleSts", False)
        self.write_signal_by_name(slot_key, "PriorityModeSts", False)
        self.write_signal_by_name(slot_key, "LogoutTrigger", False)

    async def _start_pending_command(self, slot_key: str) -> None:
        pending = self.pending_commands.get(slot_key)
        if not pending or pending.active:
            self.write_signal_by_name(slot_key, "StartProcess", False)
            return

        pending.active = True
        self.write_signal_by_name(slot_key, "CommandAccepted", True)
        self.write_signal_by_name(slot_key, "CommandRejected", False)
        self.write_signal_by_name(slot_key, "CommandFailed", False)
        self.write_signal_by_name(slot_key, "ErrorAlarm", False)
        self.write_signal_by_name(slot_key, "ErrorCode", 0)

        if pending.command_type == "Inbound" and not pending.auto_barcode_sent:
            self._set_barcode(slot_key, self.default_barcode)
            pending.auto_barcode_sent = True
        elif pending.command_type == "PalletCheck":
            self.write_signal_by_name(slot_key, "AvailablePallet", True)
            self.write_signal_by_name(slot_key, "UnavailablePallet", False)
            await self._schedule_completion(slot_key, "PalletCheckCompleted")
        elif pending.command_type == "Outbound":
            await self._schedule_completion(slot_key, "OutboundCompleted", update_location="clear")
        elif pending.command_type == "Transfer":
            await self._schedule_completion(slot_key, "TransferCompleted", update_location="target")

        self.write_signal_by_name(slot_key, "StartProcess", False)
        self.write_signal_by_name(slot_key, "CommandAccepted", False)

    async def _complete_inbound(self, slot_key: str, valid: bool) -> None:
        pending = self.pending_commands.get(slot_key)
        if not pending or pending.command_type != "Inbound":
            return

        if not valid:
            self._reset_barcode(slot_key)
            return

        await self._schedule_completion(slot_key, "InboundCompleted", update_location="target")
        self.write_signal_by_name(slot_key, "BarcodeValid", False)
        self.write_signal_by_name(slot_key, "BarcodeInvalid", False)
        self._reset_barcode(slot_key)

    async def _schedule_completion(self, slot_key: str, completion_signal: str, update_location: Optional[str] = None) -> None:
        if slot_key in self.command_tasks and not self.command_tasks[slot_key].done():
            return

        async def runner() -> None:
            await asyncio.sleep(self.auto_complete_delay)
            if update_location == "target":
                self._copy_target_to_current(slot_key)
            elif update_location == "clear":
                self._clear_current_location(slot_key)

            self.write_signal_by_name(slot_key, completion_signal, True)
            self.write_signal_by_name(slot_key, "DeviceReady", True)
            await asyncio.sleep(0.6)
            self.write_signal_by_name(slot_key, completion_signal, False)
            self._reset_runtime_flags(slot_key)
            self.pending_commands[slot_key] = None

        self.command_tasks[slot_key] = asyncio.create_task(runner())

    def _copy_target_to_current(self, slot_key: str) -> None:
        for source_name, target_name in (
            ("TargetFloor", "CurrentFloor"),
            ("TargetRail", "CurrentRail"),
            ("TargetBlock", "CurrentBlock"),
        ):
            value = self.read_signal(slot_key, source_name)
            if value is not None:
                self.write_signal_by_name(slot_key, target_name, value)

        target_depth = self.read_signal(slot_key, "SourceDepth")
        if target_depth is not None:
            self.write_signal_by_name(slot_key, "CurrentDepth", target_depth)

    def _clear_current_location(self, slot_key: str) -> None:
        for name in ("CurrentFloor", "CurrentRail", "CurrentBlock", "CurrentDepth"):
            self.write_signal_by_name(slot_key, name, 0)

    def _reset_runtime_flags(self, slot_key: str) -> None:
        for name in (
            "InboundTrigger",
            "OutboundTrigger",
            "TransferTrigger",
            "PalletCheckTrigger",
            "StartProcess",
            "CommandAccepted",
            "CommandRejected",
            "AvailablePallet",
            "UnavailablePallet",
            "CommandFailed",
            "ErrorAlarm",
            "BarcodeValid",
            "BarcodeInvalid",
        ):
            self.write_signal_by_name(slot_key, name, False)
        self.write_signal_by_name(slot_key, "ErrorCode", 0)
        self.write_signal_by_name(slot_key, "DeviceReady", True)

    def _set_barcode(self, slot_key: str, barcode: str) -> None:
        padded = list((barcode or "")[:10].ljust(10, "0"))
        for index, char in enumerate(padded, start=1):
            self.write_signal_by_name(slot_key, f"BarcodeChar{index}", char)

    def _reset_barcode(self, slot_key: str) -> None:
        for index in range(1, 11):
            self.write_signal_by_name(slot_key, f"BarcodeChar{index}", "0")


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, simulator: HeadlessPlcSimulator) -> None:
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            response = await simulator.process_command(line.decode().strip())
            writer.write((response + "\n").encode())
            await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Headless PLC simulator compatible with TQG.PlcEmulator.CrossPlatform")
    parser.add_argument("--signals", default=str(DEFAULT_SIGNALS_PATH), help="Path to signals.json from simulator project")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int, help="Bind port")
    parser.add_argument("--auth-key", default=DEFAULT_AUTH_KEY, help="Expected DB31 auth key")
    parser.add_argument("--barcode", default=DEFAULT_BARCODE, help="Default barcode emitted for inbound flow")
    parser.add_argument("--auto-complete-delay", default=1.0, type=float, help="Seconds before a command auto-completes")
    args = parser.parse_args()

    signals_path = Path(os.path.expanduser(args.signals)).resolve()
    mapping = SignalMapping.load(signals_path)
    simulator = HeadlessPlcSimulator(
        mapping=mapping,
        auth_key=args.auth_key,
        default_barcode=args.barcode,
        auto_complete_delay=args.auto_complete_delay,
    )

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, simulator),
        host=args.host,
        port=args.port,
    )

    addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    print(f"Headless PLC simulator listening on {addresses}")
    print(f"Using signals: {signals_path}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
