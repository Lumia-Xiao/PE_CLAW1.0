# Semiconductor Library

This package contains the reusable semiconductor device library used by the PE-Claw device stage.

## Structure

- `models.py`
  Common static and dynamic device dataclasses.
- `power_device.py`
  Shared `PowerDevice` wrapper used by selector, loss evaluation, and geometry code.
- `lookup_table.py`
  Reusable bounded interpolation tables for XML-derived models.
- `xml_parser.py`
  Shared parser for the PLECS XML format currently used by the device library.
- `device_builders.py`
  Shared helpers for resolving packaged XML files and building `PowerDevice` objects.
- `registry.py`
  Top-level registry composition. It gathers devices from vendor packages.
- `templates/`
  Copyable examples for future device additions. These files are not auto-registered.
- `infineon/`
  Vendor package for Infineon devices.
- `navitas/`
  Vendor package for Navitas devices.

## Current device layout

The active pattern is family-based rather than one-module-per-device.

Each vendor package is composed from explicit family modules, where each family module is the source of truth for:

- one curated static manifest
- one packaged XML subdirectory
- one family builder that registers all valid devices for that vendor/series/voltage class

Current Infineon examples:

- `infineon/coolmos8_600v.py`
- `infineon/coolmos8_650v.py`
- `infineon/coolmos_cfd7_650v.py`
- `infineon/coolmos_s7a_600v.py`
- `infineon/coolgan_650v.py`
- `infineon/coolsic_mosfet_g2_650v.py`
- `infineon/coolsic_mosfet_g2_750v.py`

Current Navitas example:

- `navitas/gen3f_sic_mosfet.py`

Example family organization:

- `infineon/coolmos8_600v.py`
  - defines `COOLMOS8_600V_STATIC_MANIFEST`
  - resolves XML assets under `infineon/data/coolmos8_600v/`
  - exposes `build_infineon_coolmos8_600v_devices()`

## How registration works

1. Add or extend the appropriate family module under the vendor package.
2. If the family uses PLECS XML models, add the XML assets under the vendor package's `data/<family_or_series>/` folder.
3. Keep the family manifest explicit and curated in that family module.
4. Import the family builder in the vendor package `__init__.py`.
5. Add the family builder to the vendor's `get_<vendor>_devices()` list.
6. The top-level `build_default_semiconductor_registry()` function will compose all vendor packages into one registry.

For the Infineon package today, registration happens in `infineon/__init__.py` via `get_infineon_devices()`.
For the Navitas package, registration happens in `navitas/__init__.py` via `get_navitas_devices()`.

## Minimal data required for a new family addition

Required:

- one explicit static manifest that covers the family devices
- a public family builder function such as `build_vendor_family_devices()`
- packaged XML assets resolved from `data/<family_or_series>/`, or another valid `DeviceDynamicModel` construction path

Optional but useful:

- package names that the semiconductor geometry view can recognize
- additional metadata fields in the static record when the shared models grow

## Recommended pattern for a new family addition

1. Copy or mirror an existing family module under the target vendor package.
2. Rename the family builder and family-specific constants.
3. Replace the placeholder static values with curated family manifest rows.
4. Add the correct XML files under the vendor `data/<family_or_series>/` folder.
5. Register the family builder from the vendor `__init__.py`.

Example:

- extend `infineon/coolmos8_600v.py`
- add or update `infineon/data/coolmos8_600v/*.xml`
- import `build_infineon_coolmos8_600v_devices` from `infineon/__init__.py`
- append it to `get_infineon_devices()`
- repeat the same pattern for other vendors such as `navitas/gen3f_sic_mosfet.py`
