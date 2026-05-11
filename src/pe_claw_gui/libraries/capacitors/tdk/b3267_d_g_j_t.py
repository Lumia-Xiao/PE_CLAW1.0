"""TDK B3267*D/G/J/T rectangular radial DC-link high-power film capacitor records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate

_IRMS_BASIS = "IRMS,max at 70 C and 10 kHz for dT <=20 C when dESRtyp <= +/-5%"
_LOSS_NOTE = "TDK B3267*D/G/J/T loss uses datasheet ESRtyp at 70 C and 10 kHz; high-frequency spectral loss remains first-pass."
_THERMAL_FALLBACK_NOTE = "No exact B3267*D/G/J/T G heat-coefficient table match for this box size; thermal-sensitive selection uses a conservative placeholder Rth."

_DVDT_BY_TYPE_AND_VOLTAGE = {
    "B32674": {300.0: 40.0, 450.0: 75.0, 630.0: 100.0, 750.0: 125.0, 875.0: 150.0},
    "B32676": {300.0: 22.0, 450.0: 54.0, 630.0: 73.0, 750.0: 85.0, 875.0: 100.0},
    "B32678": {300.0: 15.0, 450.0: 35.0, 630.0: 50.0, 750.0: 60.0, 875.0: 70.0},
}

_HEAT_COEFFICIENT_MW_PER_C_BY_SIZE_MM = {
    (11.0, 19.0, 31.5): 25.0,
    (11.0, 21.0, 31.5): 28.0,
    (12.5, 21.5, 31.5): 30.0,
    (13.5, 23.0, 31.5): 32.0,
    (14.0, 24.5, 31.5): 35.0,
    (15.0, 24.5, 31.5): 36.0,
    (16.0, 32.0, 31.5): 45.0,
    (18.0, 27.5, 31.5): 44.0,
    (18.0, 33.0, 31.5): 48.0,
    (19.0, 30.0, 31.5): 48.0,
    (20.0, 11.0, 31.5): 65.0,
    (21.0, 31.0, 31.5): 51.0,
    (22.0, 36.5, 31.5): 58.0,
    (12.0, 22.0, 41.5): 70.0,
    (14.0, 25.0, 41.5): 43.0,
    (16.0, 28.5, 41.5): 50.0,
    (18.0, 32.5, 41.5): 59.0,
    (20.0, 39.5, 42.0): 72.0,
    (24.0, 19.0, 41.5): 50.0,
    (24.0, 15.0, 41.5): 44.0,
    (28.0, 37.0, 42.0): 83.0,
    (28.0, 42.5, 42.0): 90.0,
    (30.0, 45.0, 42.0): 100.0,
    (33.0, 48.0, 42.0): 110.0,
    (43.0, 22.0, 41.5): 80.0,
    (30.0, 45.0, 57.5): 125.0,
    (35.0, 50.0, 57.5): 145.0,
    (43.0, 24.0, 57.5): 103.0,
    (45.0, 57.0, 57.5): 185.0,
    (60.0, 45.0, 57.5): 192.0,
    (130.0, 24.0, 57.5): 200.0,
    (130.0, 58.0, 57.5): 300.0,
}

_RAW_ROWS = """
B32674D,300,450,2.2,11.0,19.0,31.5,-,B32674D3225+000,5.0,18.1,16.0,0.7,4.1,1280,False
B32674D,300,450,3.3,12.5,21.5,31.5,-,B32674D3335+000,7.0,12.2,19.0,0.7,4.1,1120,False
B32674D,300,450,4.7,14.0,24.5,31.5,-,B32674D3475+000,8.5,8.9,21.0,0.7,4.2,1040,False
B32674D,300,450,5.0,15.0,24.5,31.5,-,B32674D3505+000,9.0,8.4,21.0,0.7,4.2,960,False
B32674D,300,450,6.8,18.0,27.5,31.5,-,B32674D3685+000,11.5,6.3,24.0,0.7,4.4,800,False
B32674D,300,450,8.0,16.0,32.0,31.5,-,B32674D3805+000,12.5,5.6,27.0,0.7,4.5,880,False
B32674D,300,450,8.2,18.0,33.0,31.5,-,B32674D3825+000,13.0,5.5,27.0,0.7,4.5,800,False
B32674D,300,450,10.0,21.0,31.0,31.5,-,B32674D3106+000,14.5,4.6,27.0,0.8,4.6,720,False
B32674D,300,450,12.0,22.0,36.5,31.5,-,B32674D3126+000,17.0,4.0,31.0,0.8,4.9,640,False
B32674D,450,630,1.5,11.0,19.0,31.5,-,B32674D4155+000,4.5,22.1,16.0,0.6,3.3,1280,False
B32674D,450,630,2.2,12.5,21.5,31.5,-,B32674D4225+000,6.0,14.9,19.0,0.6,3.3,1120,False
B32674D,450,630,3.3,15.0,24.5,31.5,-,B32674D4335+000,8.0,10.3,22.0,0.6,3.4,960,False
B32674D,450,630,4.7,18.0,27.5,31.5,-,B32674D4475+000,10.5,7.5,24.0,0.6,3.5,800,False
B32674D,450,630,5.0,16.0,32.0,31.5,-,B32674D4505+000,11.0,7.1,28.0,0.7,3.6,880,False
B32674D,450,630,5.6,18.0,33.0,31.5,-,B32674D4565+000,12.0,6.3,29.0,0.7,3.6,800,False
B32674D,450,630,6.0,21.0,31.0,31.5,-,B32674D4605+000,13.0,5.9,28.0,0.7,3.6,720,False
B32674D,450,630,6.8,22.0,36.5,31.5,-,B32674D4685+000,14.5,5.4,29.0,0.7,3.7,640,False
B32674D,450,630,7.5,22.0,36.5,31.5,-,B32674D4755+000,15.0,5.0,32.0,0.7,3.8,640,False
B32674D,630,800,1.0,11.0,19.0,31.5,-,B32674D6105+000,4.0,26.1,17.0,0.6,2.7,1280,False
B32674D,630,800,1.5,12.5,21.5,31.5,-,B32674D6155+000,5.5,17.9,19.0,0.6,2.7,1120,False
B32674D,630,800,2.2,15.0,24.5,31.5,-,B32674D6225+000,7.5,12.4,21.0,0.6,2.7,960,False
B32674D,630,800,3.3,16.0,32.0,31.5,-,B32674D6335+000,10.0,8.5,28.0,0.6,2.8,880,False
B32674D,630,800,4.7,22.0,36.5,31.5,-,B32674D6475+000,13.5,6.0,31.0,0.6,3.0,640,False
B32674D,630,800,5.0,22.0,36.5,31.5,-,B32674D6505+000,14.5,5.8,31.0,0.6,3.0,640,False
B32674D,750,900,0.68,11.0,19.0,31.5,-,B32674D1684+000,3.5,34.7,17.0,0.5,2.4,1280,False
B32674D,750,900,1.0,12.5,21.5,31.5,-,B32674D1105+000,4.5,24.2,18.0,0.5,2.5,1120,False
B32674D,750,900,1.5,14.0,24.5,31.5,-,B32674D1155+000,6.5,16.3,22.0,0.6,2.5,1040,False
B32674D,750,900,2.2,18.0,27.5,31.5,-,B32674D1225+000,8.5,11.3,24.0,0.6,2.5,800,False
B32674D,750,900,3.3,21.0,31.0,31.5,-,B32674D1335+000,11.0,7.9,28.0,0.6,2.6,720,False
B32674D,750,900,4.0,22.0,36.5,31.5,-,B32674D1405+000,13.0,6.7,32.0,0.6,2.7,640,False
B32674D,875,1050,0.47,11.0,19.0,31.5,-,B32674D8474+000,3.0,45.2,16.0,0.5,2.2,1280,False
B32674D,875,1050,0.68,11.0,21.0,31.5,-,B32674D8684+000,4.0,31.5,19.0,0.5,2.2,1280,False
B32674D,875,1050,1.0,13.5,23.0,31.5,-,B32674D8105+000,5.0,22.2,20.0,0.5,2.2,1040,False
B32674D,875,1050,1.5,18.0,27.5,31.5,-,B32674D8155+000,7.5,14.7,23.0,0.5,2.2,800,False
B32674D,875,1050,2.2,18.0,33.0,31.5,-,B32674D8225+000,9.5,10.3,29.0,0.5,2.3,800,False
B32674D,875,1050,3.0,22.0,36.5,31.5,-,B32674D8305+000,12.0,7.8,31.0,0.5,2.4,640,False
B32676T,300,450,6.2,24.0,15.0,41.5,-,B32676T3625+000,8.0,12.6,18.0,1.1,8.2,1040,False
B32676T,300,450,9.0,24.0,19.0,41.5,-,B32676T3905+000,10.0,9.1,19.0,1.1,8.3,780,False
B32676G,300,450,15.0,20.0,39.5,42.0,10.2,B32676G3156+000,16.0,5.4,10.0,1.1,8.3,640,False
B32676G,300,450,20.0,28.0,37.0,42.0,10.2,B32676G3206+000,20.0,4.0,11.0,1.1,8.4,440,False
B32676T,300,450,20.0,43.0,22.0,41.5,20.3,B32676T3206K000,19.5,4.0,13.0,1.1,8.3,280,False
B32676G,300,450,22.0,28.0,42.5,42.0,10.2,B32676G3226+000,21.5,3.8,11.0,1.2,8.5,440,False
B32676G,300,450,25.0,28.0,42.5,42.0,10.2,B32676G3256+000,22.5,3.4,12.0,1.2,8.6,440,False
B32676G,300,450,30.0,30.0,45.0,42.0,20.3,B32676G3306+000,26.0,2.8,12.0,1.2,8.7,400,False
B32676G,300,450,35.0,33.0,48.0,42.0,20.3,B32676G3356+000,29.5,2.5,13.0,1.2,8.8,180,False
B32676T,450,630,4.0,24.0,15.0,41.5,-,B32676T4405+000,7.0,15.5,19.0,1.0,6.6,1040,False
B32676T,450,630,4.7,24.0,19.0,41.5,-,B32676T4475+000,8.0,13.2,18.0,1.0,6.6,780,False
B32676G,450,630,8.2,20.0,39.5,42.0,10.2,B32676G4825+000,13.5,7.8,9.0,1.0,6.7,640,False
B32676G,450,630,10.0,20.0,39.5,42.0,10.2,B32676G4106+000,14.5,6.4,11.0,1.0,6.7,640,False
B32676T,450,630,13.0,43.0,22.0,41.5,20.3,B32676T4136K000,17.5,5.0,13.0,1.0,6.6,280,False
B32676G,450,630,15.0,28.0,42.5,42.0,10.2,B32676G4156+000,20.0,4.4,11.0,1.0,6.8,440,False
B32676G,450,630,20.0,30.0,45.0,42.0,20.3,B32676G4206K000,24.0,3.3,13.0,1.0,6.9,400,False
B32676G,450,630,25.0,33.0,48.0,42.0,20.3,B32676G4256K000,28.0,2.8,14.0,1.0,7.1,180,False
B32676T,630,800,2.7,24.0,15.0,41.5,-,B32676T6275+000,7.0,17.7,20.0,0.8,5.1,1040,False
B32676T,630,800,3.5,24.0,19.0,41.5,-,B32676T6355+000,8.0,14.1,19.0,0.8,5.1,780,False
B32676G,630,800,6.8,20.0,39.5,42.0,10.2,B32676G6685+000,13.5,7.4,10.0,0.8,5.2,640,False
B32676G,630,800,7.5,20.0,39.5,42.0,10.2,B32676G6755+000,14.5,6.6,12.0,0.8,5.2,640,False
B32676G,630,800,8.2,28.0,37.0,42.0,10.2,B32676G6825+000,16.0,6.1,11.0,0.8,5.2,440,False
B32676T,630,800,9.0,43.0,22.0,41.5,20.3,B32676T6905K000,16.5,5.7,13.0,0.8,5.1,280,False
B32676G,630,800,10.0,28.0,42.5,42.0,10.2,B32676G6106+000,18.5,5.1,11.0,0.8,5.2,440,False
B32676G,630,800,12.0,28.0,42.5,42.0,10.2,B32676G6126+000,20.0,4.4,12.0,0.8,5.3,440,False
B32676G,630,800,14.0,30.0,45.0,42.0,20.3,B32676G6146+000,23.0,3.7,14.0,0.8,5.3,400,False
B32676G,630,800,15.0,33.0,48.0,42.0,20.3,B32676G6156+000,25.0,3.5,14.0,0.8,5.4,180,False
B32676T,750,900,2.0,24.0,15.0,41.5,-,B32676T1205+000,6.0,22.7,18.0,0.8,4.6,1040,False
B32676T,750,900,2.7,24.0,19.0,41.5,-,B32676T1275+000,7.5,16.7,19.0,0.8,4.6,780,False
B32676G,750,900,4.7,20.0,39.5,42.0,10.2,B32676G1475+000,12.0,9.5,10.0,0.8,4.6,640,False
B32676G,750,900,5.6,20.0,39.5,42.0,10.2,B32676G1565+000,13.0,8.2,11.0,0.8,4.7,640,False
B32676G,750,900,6.8,28.0,37.0,42.0,10.2,B32676G1685+000,15.5,6.7,11.0,0.8,4.7,440,False
B32676G,750,900,9.0,30.0,45.0,42.0,20.3,B32676G1905+000,19.5,5.1,12.0,0.8,4.7,440,False
B32676G,750,900,10.0,30.0,45.0,42.0,20.3,B32676G1106+000,20.5,4.7,13.0,0.8,4.8,400,False
B32676G,750,900,12.0,33.0,48.0,42.0,20.3,B32676G1126+000,23.0,4.0,14.0,0.8,4.8,180,False
B32676T,875,1050,1.5,24.0,15.0,41.5,-,B32676T8155+000,5.5,26.2,18.0,0.7,4.1,1040,False
B32676T,875,1050,2.0,24.0,19.0,41.5,-,B32676T8205+000,7.0,19.6,19.0,0.7,4.1,780,False
B32676G,875,1050,3.3,20.0,39.5,42.0,10.2,B32676G8335+000,10.5,12.0,13.0,0.7,4.1,640,False
B32676G,875,1050,4.0,20.0,39.5,42.0,10.2,B32676G8405+000,12.0,9.9,11.0,0.7,4.1,640,False
B32676G,875,1050,4.7,28.0,37.0,42.0,10.2,B32676G8475+000,13.5,8.6,10.0,0.7,4.1,440,False
B32676G,875,1050,6.8,28.0,42.5,42.0,10.2,B32676G8685+000,17.0,6.0,12.0,0.7,4.2,440,False
B32676G,875,1050,7.5,30.0,45.0,42.0,20.3,B32676G8755+000,19.0,5.4,13.0,0.7,4.2,400,False
B32676G,875,1050,10.0,33.0,48.0,42.0,20.3,B32676G8106K000,22.5,4.3,14.0,0.7,4.3,180,False
B32678T,300,450,30.0,43.0,24.0,57.5,-,B32678T3306K000,22.5,3.9,13.0,1.5,11.8,560,False
B32678G,300,450,40.0,30.0,45.0,57.5,-,B32678G3406+000,28.0,3.0,12.0,1.5,12.3,280,False
B32678G,300,450,47.0,35.0,50.0,57.5,-,B32678G3476+000,33.0,2.6,13.0,1.5,12.5,108,False
B32678G,300,450,60.0,35.0,50.0,57.5,-,B32678G3606K000,37.0,2.1,15.0,1.6,12.9,108,False
B32678G,300,450,80.0,45.0,57.0,57.5,-,B32678G3806+000,47.0,1.6,18.0,1.6,13.5,140,False
B32678J,300,450,80.0,130.0,24.0,57.5,-,B32678J3806K000,51.0,1.4,4.0,1.5,11.7,80,False
B32678G,300,450,100.0,60.0,45.0,57.5,-,B32678G3107+000,48.0,1.4,19.0,1.6,13.5,200,False
B32678J,300,450,270.0,130.0,58.0,57.5,-,B32678J3277K000,108.0,0.5,6.0,1.6,13.8,40,False
B32678T,450,630,20.0,43.0,24.0,57.5,-,B32678T4206K000,20.0,4.9,13.0,1.3,9.8,560,False
B32678G,450,630,30.0,35.0,50.0,57.5,-,B32678G4306+000,28.0,3.2,14.0,1.3,9.9,108,False
B32678G,450,630,35.0,35.0,50.0,57.5,-,B32678G4356+000,31.5,2.8,14.0,1.3,10.0,108,False
B32678G,450,630,40.0,35.0,50.0,57.5,-,B32678G4406K000,34.0,2.5,15.0,1.3,10.2,108,False
B32678G,450,630,60.0,45.0,57.0,57.5,-,B32678G4606+000,45.0,1.8,18.0,1.4,11.2,140,False
B32678J,450,630,60.0,130.0,24.0,57.5,-,B32678J4606K000,49.5,1.6,4.0,1.2,9.5,80,False
B32678G,450,630,65.0,60.0,45.0,57.5,-,B32678G4656+000,48.0,1.6,19.0,1.3,10.6,200,False
B32678J,450,630,180.0,130.0,58.0,57.5,-,B32678J4187K000,97.5,0.6,6.0,1.4,11.2,40,False
B32678T,630,800,13.0,43.0,24.0,57.5,-,B32678T6136K000,18.0,5.9,13.0,1.1,7.9,560,False
B32678G,630,800,20.0,35.0,50.0,57.5,-,B32678G6206+000,26.5,4.0,13.0,1.1,8.2,108,False
B32678G,630,800,25.0,35.0,50.0,57.5,-,B32678G6256+000,29.5,3.3,15.0,1.1,8.3,108,False
B32678J,630,800,38.0,130.0,24.0,57.5,-,B32678J6386K000,43.5,2.1,4.0,1.1,7.9,80,False
B32678G,630,800,40.0,45.0,57.0,57.5,-,B32678G6406+000,41.0,2.1,18.0,1.2,8.8,140,False
B32678G,630,800,45.0,60.0,45.0,57.5,-,B32678G6456+000,43.0,1.9,19.0,1.2,8.7,200,False
B32678J,630,800,120.0,130.0,58.0,57.5,-,B32678J6127K000,90.0,0.7,6.0,1.2,8.8,40,False
B32678T,750,900,9.0,43.0,24.0,57.5,-,B32678T1905K000,16.5,7.2,13.0,1.0,6.8,560,False
B32678G,750,900,15.0,30.0,45.0,57.5,-,B32678G1156K000,23.0,4.5,14.0,1.0,7.0,280,False
B32678G,750,900,20.0,35.0,50.0,57.5,-,B32678G1206K000,28.0,3.5,15.0,1.0,7.2,108,False
B32678G,750,900,28.0,45.0,57.0,57.5,-,B32678G1286+000,37.5,2.5,18.0,1.0,7.4,140,False
B32678G,750,900,30.0,60.0,45.0,57.5,-,B32678G1306+000,39.5,2.4,19.0,1.0,7.3,200,False
B32678J,750,900,30.0,130.0,24.0,57.5,-,B32678J1306K000,40.5,2.3,4.0,1.0,6.8,80,False
B32678J,750,900,85.0,130.0,58.0,57.5,-,B32678J1856K000,82.5,0.9,6.0,1.0,7.4,40,False
B32678T,875,1050,7.0,43.0,24.0,57.5,-,B32678T8705K000,15.5,8.2,9.0,0.9,6.0,560,True
B32678G,875,1050,15.0,35.0,50.0,57.5,-,B32678G8156K000,26.5,4.0,15.0,0.9,6.3,108,False
B32678G,875,1050,22.0,45.0,57.0,57.5,-,B32678G8226+000,35.0,2.9,17.0,1.0,6.5,140,False
B32678J,875,1050,22.0,130.0,24.0,57.5,-,B32678J8226K000,39.0,2.6,5.0,0.9,6.0,80,True
B32678G,875,1050,24.0,60.0,45.0,57.5,-,B32678G8246+000,38.0,2.6,19.0,0.9,6.4,200,False
B32678J,875,1050,65.0,130.0,58.0,57.5,-,B32678J8656K000,78.0,1.0,6.0,1.0,6.5,40,True
""".strip()


def _candidate(row: str) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 16:
        raise ValueError(f"Invalid B3267*D/G/J/T row: {row}")
    (
        subtype,
        voltage_dc_v,
        voltage_70c_v,
        capacitance_uf,
        width_w_mm,
        height_h_mm,
        length_l_mm,
        p1_mm,
        part_number,
        irms_a,
        esr_mohm,
        esl_nh,
        tan_delta_1khz,
        tan_delta_10khz,
        spq,
        dual_use_restricted,
    ) = fields
    voltage_v = float(voltage_dc_v)
    capacitance_value_uf = float(capacitance_uf)
    body_width_mm = float(width_w_mm)
    body_height_mm = float(height_h_mm)
    body_depth_mm = float(length_l_mm)
    heat_coefficient_mw_per_c = _heat_coefficient_mw_per_c(body_width_mm, body_height_mm, body_depth_mm)
    rth_c_per_w = 1000.0 / heat_coefficient_mw_per_c if heat_coefficient_mw_per_c is not None else 1e9
    dvdt_v_per_us = _DVDT_BY_TYPE_AND_VOLTAGE[subtype[:6]][voltage_v]
    secondary_spacing_mm = None if p1_mm in {"-", "*"} else float(p1_mm)
    terminal_count = _terminal_count(subtype, secondary_spacing_mm)
    lead_diameter_mm = _lead_diameter_mm(subtype, terminal_count)
    tan_delta_1khz_value = float(tan_delta_1khz) * 1e-3
    tan_delta_10khz_value = float(tan_delta_10khz) * 1e-3
    operating_voltage_105c_v = voltage_v * (1.0 - 0.012 * 20.0)
    notes = [
        _LOSS_NOTE,
        f"Vop_70c_v={float(voltage_70c_v):.6g}.",
        f"tan_delta_1khz={tan_delta_1khz_value:.6g}; tan_delta_10khz={tan_delta_10khz_value:.6g}.",
        "Rectangular dimensions use w as width, l as depth, and h as height for first-pass geometry.",
    ]
    if heat_coefficient_mw_per_c is None:
        notes.append(_THERMAL_FALLBACK_NOTE)
    else:
        notes.append(f"Equivalent heat coefficient G={heat_coefficient_mw_per_c:.6g} mW/C; Rth=1000/G.")
    if dual_use_restricted == "True":
        notes.append("dual_use_restricted=True; datasheet ordering code carries the dual-use export restriction marker.")
    if subtype.endswith("T"):
        notes.append("Low-profile T-variant geometry is flagged from the datasheet ordering table/dimensional family.")
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="TDK",
        series="B3267*D/G/J/T",
        capacitor_type="film",
        construction="metallized_polypropylene_mkp",
        application="DC link",
        application_category="dc_link",
        application_notes="Rectangular plastic-box radial-lead TDK MKP high-power DC-link capacitor.",
        capacitance_f=capacitance_value_uf * 1e-6,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        operating_voltage_105c_v=operating_voltage_105c_v,
        surge_voltage_v=1.5 * voltage_v,
        ipkr_a=capacitance_value_uf * dvdt_v_per_us,
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=float(irms_a),
        irms_rating_basis=_IRMS_BASIS,
        pmax_w=20.0 / rth_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=dvdt_v_per_us,
        tolerance_percent=_tolerance_percent(part_number),
        hotspot_temp_max_c=105.0,
        tan_delta_0=tan_delta_10khz_value,
        tan_delta_frequency_hz=10_000.0,
        esr_frequency_hz=10_000.0,
        automotive_grade=True,
        self_heating_limit_c=20.0,
        ripple_voltage_limit_ratio=0.2,
        source="TDK Film Capacitors, Capacitors for DC Link, B3267*D/G/J/T datasheet, April 2025",
        source_pdf="MKP_B32674_678.pdf",
        notes=notes,
        package_shape="rectangular_box",
        case_type=subtype,
        low_profile=subtype.endswith("T"),
        terminal_type="radial_tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="plastic_box",
        recommended_orientation="any_position",
        clearance_note="Follow PCB creepage, clearance, and lead-forming rules from the datasheet and application design.",
        terminal_count=terminal_count,
        terminal_diameter_mm=lead_diameter_mm,
        terminal_pitch_mm=_lead_spacing_mm(subtype),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_width_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_depth_mm,
        lead_spacing_mm=_lead_spacing_mm(subtype),
        lead_spacing_secondary_mm=secondary_spacing_mm,
        lead_spacing_s_mm=_lead_spacing_mm(subtype),
        lead_spacing_s1_mm=secondary_spacing_mm,
        lead_length_mm=6.0,
        lead_length_ll_mm=6.0,
        lead_diameter_mm=lead_diameter_mm,
        lead_diameter_f_mm=lead_diameter_mm,
        total_volume_cm3=body_width_mm * body_height_mm * body_depth_mm / 1000.0,
        body_color="plastic_box",
        spq=int(spq),
    )


def _lead_spacing_mm(subtype: str) -> float:
    if subtype == "B32674D":
        return 27.5
    if subtype.startswith("B32676"):
        return 37.5
    if subtype.startswith("B32678"):
        return 52.5
    raise ValueError(f"Unsupported B3267 subtype: {subtype}")


def _terminal_count(subtype: str, secondary_spacing_mm: float | None) -> int:
    if subtype == "B32674D":
        return 2
    if subtype == "B32678J":
        return 12
    if subtype == "B32676T" and secondary_spacing_mm is None:
        return 2
    if subtype.startswith("B32676") or subtype.startswith("B32678"):
        return 4
    raise ValueError(f"Unsupported B3267 terminal geometry: {subtype}")


def _lead_diameter_mm(subtype: str, terminal_count: int) -> float:
    if subtype == "B32674D":
        return 0.8
    if subtype == "B32676T" and terminal_count == 2:
        return 1.0
    if subtype.startswith("B32676") or subtype.startswith("B32678"):
        return 1.2
    raise ValueError(f"Unsupported B3267 lead diameter: {subtype} {terminal_count}")


def _tolerance_percent(part_number: str) -> float:
    if part_number.endswith("J000"):
        return 5.0
    if part_number.endswith("K000"):
        return 10.0
    return 0.0


def _heat_coefficient_mw_per_c(width_mm: float, height_mm: float, length_mm: float) -> float | None:
    return _HEAT_COEFFICIENT_MW_PER_C_BY_SIZE_MM.get((width_mm, height_mm, length_mm))


def get_b3267_d_g_j_t_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK B3267*D/G/J/T capacitor candidates."""

    return tuple(_candidate(row) for row in _RAW_ROWS.splitlines() if row.strip())


B3267_D_G_J_T_CAPACITORS = get_b3267_d_g_j_t_capacitors()

__all__ = ["B3267_D_G_J_T_CAPACITORS", "get_b3267_d_g_j_t_capacitors"]
