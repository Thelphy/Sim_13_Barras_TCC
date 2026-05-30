from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class BusData:
    id: int
    name: str
    vn_kv: float
    type: str # 'slack', 'pq', 'pv'
    p_load_kw: float = 0.0
    q_load_kvar: float = 0.0
    p_gen_kw: float = 0.0
    v_target_pu: float = 1.0
    gen_enabled: bool = True
    p_load_enabled: bool = True
    q_load_enabled: bool = True

@dataclass
class LineData:
    id: int
    from_bus: int
    to_bus: int
    length_km: float
    r_ohm_per_km: float
    x_ohm_per_km: float
    c_nf_per_km: float = 10.0
    max_i_ka: float = 1.0
    is_transformer: bool = False

@dataclass
class SystemState:
    buses: Dict[int, BusData] = field(default_factory=dict)
    lines: Dict[int, LineData] = field(default_factory=dict)

@dataclass
class SimulationResults:
    success: bool = False
    bus_results: List[list] = field(default_factory=list)
    line_results: List[list] = field(default_factory=list)
    eigenvalues: List[float] = field(default_factory=list)
    participation_factors: Dict[int, float] = field(default_factory=dict)
    pv_curve_p: List[float] = field(default_factory=list)
    pv_curve_v: List[float] = field(default_factory=list)
