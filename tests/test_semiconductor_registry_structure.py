from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.libraries.semiconductors.infineon import get_infineon_devices
from pe_claw_gui.libraries.semiconductors.mitsubishi import get_mitsubishi_devices
from pe_claw_gui.libraries.semiconductors.navitas import get_navitas_devices
from pe_claw_gui.libraries.semiconductors.rohm import get_rohm_devices
from pe_claw_gui.libraries.semiconductors.wolfspeed import get_wolfspeed_devices
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry, get_vendor_device_builders


def test_semiconductor_registry_structure_supports_vendor_enumeration() -> None:
    registry = build_default_semiconductor_registry()
    vendor_builders = get_vendor_device_builders()
    infineon_devices = get_infineon_devices()
    mitsubishi_devices = get_mitsubishi_devices()
    navitas_devices = get_navitas_devices()
    rohm_devices = get_rohm_devices()
    wolfspeed_devices = get_wolfspeed_devices()

    assert registry.devices
    assert "Infineon" in vendor_builders
    assert "Mitsubishi" in vendor_builders
    assert "Navitas" in vendor_builders
    assert "ROHM" in vendor_builders
    assert "Wolfspeed" in vendor_builders
    assert registry.get_device("IPAN60R180CM8").part_number == "IPAN60R180CM8"
    assert registry.get_device("IPD60R180CM8").part_number == "IPD60R180CM8"
    assert registry.get_device("IPD60R600CM8").part_number == "IPD60R600CM8"
    assert registry.get_device("IPDQ65R018CM8").part_number == "IPDQ65R018CM8"
    assert registry.get_device("IPW65R060CM8").part_number == "IPW65R060CM8"
    assert registry.get_device("IGT65R025D2").part_number == "IGT65R025D2"
    assert registry.get_device("IGOT65R055D2").part_number == "IGOT65R055D2"
    assert registry.get_device("CM600DY-24T").part_number == "CM600DY-24T"
    assert registry.get_device("FMF600DXE-24BN").part_number == "FMF600DXE-24BN"
    assert registry.get_device("G3F25MT06J").part_number == "G3F25MT06J"
    assert registry.get_device("G3F20MT12K").part_number == "G3F20MT12K"
    assert registry.get_device("BSM080D12P2C008").part_number == "BSM080D12P2C008"
    assert registry.get_device("RGA80TSX2EHR").part_number == "RGA80TSX2EHR"
    assert registry.get_device("SCS304AG").part_number == "SCS304AG"
    assert registry.get_device("C3M0045065J1").part_number == "C3M0045065J1"
    assert registry.list_vendors() == ["Infineon", "Mitsubishi", "Navitas", "ROHM", "Wolfspeed"]
    assert "Infineon" in registry.devices_by_vendor()
    assert "Mitsubishi" in registry.devices_by_vendor()
    assert "Navitas" in registry.devices_by_vendor()
    assert "ROHM" in registry.devices_by_vendor()
    assert "Wolfspeed" in registry.devices_by_vendor()
    assert any(device.part_number == "IPAN60R180CM8" for device in infineon_devices)
    assert any(device.part_number == "IPD60R180CM8" for device in infineon_devices)
    assert any(device.part_number == "IPD60R600CM8" for device in infineon_devices)
    assert any(device.part_number == "IPDQ65R018CM8" for device in infineon_devices)
    assert any(device.part_number == "IPW65R060CM8" for device in infineon_devices)
    assert any(device.part_number == "IGT65R025D2" for device in infineon_devices)
    assert any(device.part_number == "IGOT65R055D2" for device in infineon_devices)
    assert any(device.part_number == "CM600DY-24T" for device in mitsubishi_devices)
    assert any(device.part_number == "FMF600DXE-24BN" for device in mitsubishi_devices)
    assert any(device.part_number == "G3F25MT06J" for device in navitas_devices)
    assert any(device.part_number == "G3F20MT12K" for device in navitas_devices)
    assert rohm_devices
    assert any(device.part_number == "BSM080D12P2C008" for device in rohm_devices)
    assert any(device.part_number == "RGA80TSX2EHR" for device in rohm_devices)
    assert any(device.part_number == "SCS304AG" for device in rohm_devices)
    assert any(device.part_number == "C3M0045065J1" for device in wolfspeed_devices)
