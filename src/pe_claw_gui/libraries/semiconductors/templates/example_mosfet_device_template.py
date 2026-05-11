"""Example template for adding a new MOSFET device definition.

This file is intentionally not auto-registered. Copy it into a vendor package,
replace the placeholder values, and then import the new builder from the
vendor's ``__init__.py`` to register the device.
"""

from __future__ import annotations

from functools import lru_cache

from ..device_builders import build_power_device_from_static_and_xml
from ..models import DeviceStaticRecord
from ..power_device import PowerDevice

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.templates"
_XML_RELATIVE_PATH = "data/replace-with-device-plecs.xml"


def build_example_mosfet_static_record() -> DeviceStaticRecord:
    """Example static-record pattern for a future MOSFET device."""

    return DeviceStaticRecord(
        part_number="EXAMPLE123",
        vendor="ExampleVendor",
        device_type="MOSFET with Diode",
        technology="Example MOSFET Platform",
        package="PG-TO220-3",
        marking="EX123",
        vdss_max_V=650.0,
        id_cont_25C_A=20.0,
        id_cont_100C_A=12.0,
        id_pulse_A=50.0,
        if_cont_A=20.0,
        if_pulse_A=50.0,
        vgs_static_min_V=-20.0,
        vgs_static_max_V=20.0,
        vgs_dynamic_min_V=-30.0,
        vgs_dynamic_max_V=30.0,
        power_dissipation_25C_W=30.0,
        tj_min_C=-55.0,
        tj_max_C=150.0,
        tj_extended_max_C=175.0,
        eas_single_mJ=30.0,
        ear_repetitive_mJ=0.1,
        ias_single_A=3.0,
        dvdt_mosfet_V_per_ns=100.0,
        dvdt_diode_V_per_ns=60.0,
        didt_diode_A_per_us=1000.0,
        vgs_th_min_V=3.0,
        vgs_th_typ_V=4.0,
        vgs_th_max_V=5.0,
        rds_on_typ_25C_Ohm=0.15,
        rds_on_max_25C_Ohm=0.18,
        rds_on_typ_150C_Ohm=0.30,
        rg_int_typ_Ohm=10.0,
        ciss_typ_pF=800.0,
        coss_typ_pF=20.0,
        co_er_typ_pF=40.0,
        co_tr_typ_pF=300.0,
        td_on_ns=20.0,
        tr_ns=8.0,
        td_off_ns=80.0,
        tf_ns=15.0,
        qgs_nC=5.0,
        qgd_nC=7.0,
        qg_total_nC=18.0,
        vplateau_V=6.0,
        vsd_typ_V=0.9,
        trr_typ_ns=60.0,
        trr_max_ns=80.0,
        qrr_typ_uC=0.2,
        qrr_max_uC=0.3,
        irrm_typ_A=6.0,
        rth_jc_K_per_W=4.0,
        rth_ja_K_per_W=60.0,
        datasheet_rev="0.0",
        datasheet_date="2099-01-01",
    )


@lru_cache(maxsize=1)
def build_example_mosfet_device() -> PowerDevice:
    """Example public builder pattern for a future concrete MOSFET entry."""

    return build_power_device_from_static_and_xml(
        static_record=build_example_mosfet_static_record(),
        package_name=_DEVICE_PACKAGE,
        relative_xml_path=_XML_RELATIVE_PATH,
    )
