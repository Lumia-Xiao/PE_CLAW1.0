"""Reusable helpers for per-device semiconductor definitions."""

from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

from .models import DeviceDynamicModel, DeviceStaticRecord
from .power_device import PowerDevice
from .xml_parser import parse_plecs_xml


def resolve_device_data_resource(package_name: str, relative_path: str):
    """Resolve a package data resource for a concrete device definition."""

    return files(package_name).joinpath(relative_path)


def resolve_device_data_path(package_name: str, relative_path: str) -> Path:
    """Resolve a package data resource into a concrete filesystem path."""

    resource = resolve_device_data_resource(package_name, relative_path)
    with as_file(resource) as resolved_path:
        return Path(resolved_path)


def load_dynamic_model_from_xml(package_name: str, relative_xml_path: str) -> DeviceDynamicModel:
    """Load a reusable dynamic device model from packaged PLECS XML data."""

    resource = resolve_device_data_resource(package_name, relative_xml_path)
    with as_file(resource) as xml_path:
        return parse_plecs_xml(xml_path)


def build_power_device_from_static_and_xml(
    *,
    static_record: DeviceStaticRecord,
    package_name: str,
    relative_xml_path: str,
) -> PowerDevice:
    """Build one concrete power device from a static record and packaged XML."""

    return PowerDevice(
        static=static_record,
        dynamic=load_dynamic_model_from_xml(package_name, relative_xml_path),
    )
