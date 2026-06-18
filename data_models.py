from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
# Classe que representa os dados de cada barra do sistema
class BusData:
    """Dados das barras do sistema"""
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
# Classe que armazena as informações e parâmetros de uma linha de transmissão
class LineData:
    """Dados das linhas de transmissão"""
    id: int
    from_bus: int
    to_bus: int
    length_km: float
    r_ohm_per_km: float
    x_ohm_per_km: float
    c_nf_per_km: float = 10.0
    max_i_ka: float = 1.0
    is_transformer: bool = False
    sn_mva: float = 5.0
    vk_percent: float = 5.0
    vkr_percent: float = 1.0
    pfe_kw: float = 10.0
    i0_percent: float = 0.5

@dataclass
# Classe para armazenar os parâmetros físicos e elétricos dos cabos
class CableConfig:
    """Configurações dos cabos"""
    name: str
    r_ohm_per_km: float
    x_ohm_per_km: float

@dataclass
# Classe responsável por agregar os dados do sistema, como barras, linhas e cabos
class SystemState:
    """Estado do sistema"""
    buses: Dict[int, BusData] = field(default_factory=dict)
    lines: Dict[int, LineData] = field(default_factory=dict)
    cables: Dict[str, CableConfig] = field(default_factory=dict)

@dataclass
# Classe para armazenar os resultados do fluxo de potência e curvas da simulação
class SimulationResults:
    """Resultados da simulação"""
    success: bool = False
    bus_results: List[list] = field(default_factory=list)
    line_results: List[list] = field(default_factory=list)
    pv_curve_p: List[float] = field(default_factory=list)
    pv_curve_v: List[float] = field(default_factory=list)
