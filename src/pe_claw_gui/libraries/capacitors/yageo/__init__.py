"""KEMET / YAGEO capacitor series."""

from .c44p_t import C44P_T_CAPACITORS, list_c44p_t_capacitors
from .a50_axial import A50_AXIAL_CAPACITORS, list_a50_axial_capacitors
from .c28 import C28_CAPACITORS, list_c28_capacitors
from .c44a import C44A_CAPACITORS, list_c44a_capacitors
from .c44p_r import C44P_R_CAPACITORS, list_c44p_r_capacitors
from .c44u import C44U_CAPACITORS, list_c44u_capacitors
from .c44u_m import C44U_M_CAPACITORS, list_c44u_m_capacitors
from .c44u_t import C44U_T_CAPACITORS, list_c44u_t_capacitors
from .c4aq import C4AQ_CAPACITORS, list_c4aq_capacitors
from .c4aq_p import C4AQ_P_CAPACITORS, list_c4aq_p_capacitors
from .c4ak import C4AK_CAPACITORS, list_c4ak_capacitors
from .c4aq_m import C4AQ_M_CAPACITORS, list_c4aq_m_capacitors
from .c4as import C4AS_CAPACITORS, list_c4as_capacitors
from .c4at import C4AT_CAPACITORS, list_c4at_capacitors
from .c4au import C4AU_CAPACITORS, list_c4au_capacitors
from .c4bs import C4BS_CAPACITORS, list_c4bs_capacitors
from .c4bt import C4BT_CAPACITORS, list_c4bt_capacitors
from .c4de import C4DE_CAPACITORS, list_c4de_capacitors
from .f863h_x2_310_125c import F863H_X2_310_125C_CAPACITORS, list_f863h_x2_310_125c_capacitors
from .mdc import MDC_CAPACITORS, list_mdc_capacitors
from .r60 import R60_CAPACITORS, list_r60_capacitors
from .r66 import R66_FINAL_CAPACITORS, list_r66_capacitors
from .r71 import R71_CAPACITORS, list_r71_capacitors
from .r71h import R71H_CAPACITORS, list_r71h_capacitors
from .r73 import R73_CAPACITORS, list_r73_capacitors
from .r75 import R75_CAPACITORS, list_r75_capacitors
from .r75h import R75H_CAPACITORS, list_r75h_capacitors
from .r76 import R76_CAPACITORS, list_r76_capacitors
from .r76h import R76H_CAPACITORS, list_r76h_capacitors
from .r862_x2_310 import F862_X2_310_CAPACITORS, list_r862_x2_310_capacitors
from .r863_x2_310 import F863_X2_310_CAPACITORS, list_r863_x2_310_capacitors
from .rsb import RSB_CAPACITORS, list_rsb_capacitors
from .smr import SMR_CAPACITORS, list_smr_capacitors


def list_yageo_capacitors():
    """Return all registered KEMET / YAGEO capacitor candidates."""

    return (
        *list_c44p_t_capacitors(),
        *list_c4aq_p_capacitors(),
        *list_c4ak_capacitors(),
        *list_c4au_capacitors(),
        *list_c4aq_m_capacitors(),
        *list_c4as_capacitors(),
        *list_c4at_capacitors(),
        *list_mdc_capacitors(),
        *list_r76h_capacitors(),
        *list_r75h_capacitors(),
        *list_r71h_capacitors(),
        *list_f863h_x2_310_125c_capacitors(),
        *list_r76_capacitors(),
        *list_r71_capacitors(),
        *list_r73_capacitors(),
        *list_smr_capacitors(),
        *list_r862_x2_310_capacitors(),
        *list_r75_capacitors(),
        *list_r60_capacitors(),
        *list_r863_x2_310_capacitors(),
        *list_a50_axial_capacitors(),
        *list_c44u_t_capacitors(),
        *list_c44u_m_capacitors(),
        *list_c44p_r_capacitors(),
        *list_c28_capacitors(),
        *list_r66_capacitors(),
        *list_rsb_capacitors(),
        *list_c4bt_capacitors(),
        *list_c4bs_capacitors(),
        *list_c44u_capacitors(),
        *list_c44a_capacitors(),
        *list_c4de_capacitors(),
        *list_c4aq_capacitors(),
    )


__all__ = [
    "C44P_T_CAPACITORS",
    "A50_AXIAL_CAPACITORS",
    "C28_CAPACITORS",
    "C44A_CAPACITORS",
    "C44P_R_CAPACITORS",
    "C44U_CAPACITORS",
    "C44U_M_CAPACITORS",
    "C44U_T_CAPACITORS",
    "C4AQ_CAPACITORS",
    "C4AQ_P_CAPACITORS",
    "C4AK_CAPACITORS",
    "C4AU_CAPACITORS",
    "C4AQ_M_CAPACITORS",
    "C4AS_CAPACITORS",
    "C4AT_CAPACITORS",
    "C4BS_CAPACITORS",
    "C4BT_CAPACITORS",
    "C4DE_CAPACITORS",
    "MDC_CAPACITORS",
    "R76H_CAPACITORS",
    "R75H_CAPACITORS",
    "R71H_CAPACITORS",
    "F863H_X2_310_125C_CAPACITORS",
    "R76_CAPACITORS",
    "R71_CAPACITORS",
    "R73_CAPACITORS",
    "SMR_CAPACITORS",
    "F862_X2_310_CAPACITORS",
    "R75_CAPACITORS",
    "R60_CAPACITORS",
    "R66_FINAL_CAPACITORS",
    "F863_X2_310_CAPACITORS",
    "RSB_CAPACITORS",
    "list_c44p_t_capacitors",
    "list_a50_axial_capacitors",
    "list_c28_capacitors",
    "list_c44a_capacitors",
    "list_c44p_r_capacitors",
    "list_c44u_capacitors",
    "list_c44u_m_capacitors",
    "list_c44u_t_capacitors",
    "list_c4aq_capacitors",
    "list_c4aq_p_capacitors",
    "list_c4ak_capacitors",
    "list_c4au_capacitors",
    "list_c4aq_m_capacitors",
    "list_c4as_capacitors",
    "list_c4at_capacitors",
    "list_c4bs_capacitors",
    "list_c4bt_capacitors",
    "list_c4de_capacitors",
    "list_mdc_capacitors",
    "list_r76h_capacitors",
    "list_r75h_capacitors",
    "list_r71h_capacitors",
    "list_f863h_x2_310_125c_capacitors",
    "list_r76_capacitors",
    "list_r71_capacitors",
    "list_r73_capacitors",
    "list_smr_capacitors",
    "list_r862_x2_310_capacitors",
    "list_r75_capacitors",
    "list_r60_capacitors",
    "list_r66_capacitors",
    "list_r863_x2_310_capacitors",
    "list_rsb_capacitors",
    "list_yageo_capacitors",
]
