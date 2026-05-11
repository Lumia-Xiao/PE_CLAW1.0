"""TDK capacitor series."""

from .b25654a_001 import B25654A_001_CAPACITORS, get_b25654a_001_capacitors
from .b3267_d_g_j_t import B3267_D_G_J_T_CAPACITORS, get_b3267_d_g_j_t_capacitors
from .b3271xp import B3271XP_CAPACITORS, get_b3271xp_capacitors
from .b32714h_718h import B32714H_718H_CAPACITORS, get_b32714h_718h_capacitors
from .b3272agt import B3272AGT_CAPACITORS, get_b3272agt_capacitors
from .b3277_d_e_g_j_t import B3277_D_E_G_J_T_CAPACITORS, get_b3277_d_e_g_j_t_capacitors
from .b3277h import B3277H_CAPACITORS, get_b3277h_capacitors
from .b3277m import B3277M_CAPACITORS, get_b3277m_capacitors
from .b3277p import B3277P_CAPACITORS, get_b3277p_capacitors
from .b3277xyz import B3277XYZ_CAPACITORS, get_b3277xyz_capacitors


def list_tdk_capacitors() -> tuple:
    """Return all registered TDK capacitor candidates."""

    return (
        *get_b3271xp_capacitors(),
        *get_b3272agt_capacitors(),
        *get_b3277p_capacitors(),
        *get_b3267_d_g_j_t_capacitors(),
        *get_b32714h_718h_capacitors(),
        *get_b25654a_001_capacitors(),
        *get_b3277m_capacitors(),
        *get_b3277xyz_capacitors(),
        *get_b3277_d_e_g_j_t_capacitors(),
        *get_b3277h_capacitors(),
    )


__all__ = [
    "B25654A_001_CAPACITORS",
    "B3267_D_G_J_T_CAPACITORS",
    "B3271XP_CAPACITORS",
    "B32714H_718H_CAPACITORS",
    "B3272AGT_CAPACITORS",
    "B3277_D_E_G_J_T_CAPACITORS",
    "B3277H_CAPACITORS",
    "B3277M_CAPACITORS",
    "B3277P_CAPACITORS",
    "B3277XYZ_CAPACITORS",
    "get_b25654a_001_capacitors",
    "get_b3267_d_g_j_t_capacitors",
    "get_b3271xp_capacitors",
    "get_b32714h_718h_capacitors",
    "get_b3272agt_capacitors",
    "get_b3277_d_e_g_j_t_capacitors",
    "get_b3277h_capacitors",
    "get_b3277m_capacitors",
    "get_b3277p_capacitors",
    "get_b3277xyz_capacitors",
    "list_tdk_capacitors",
]
