import time
import pandapower as pp
import numpy as np
from engine_sep import PowerSystemEngine
from data_models import SystemState, BusData, LineData

def run_benchmark():
    engine = PowerSystemEngine()
    state = SystemState()

    # Create a large system to exaggerate iteration times
    for i in range(5000):
        state.buses[i] = BusData(id=i, name=f"Bus_{i}", vn_kv=110, type="slack" if i == 0 else "pq", p_load_kw=100, q_load_kvar=50)

    for i in range(4999):
        state.lines[i] = LineData(id=i, from_bus=i, to_bus=i+1, length_km=1, r_ohm_per_km=0.1, x_ohm_per_km=0.1)

    print("Building network...")
    engine.build_network(state)

    print("Running power flow...")
    start_pf = time.time()
    engine.run_power_flow()
    print(f"Total Power Flow and result extraction time: {time.time() - start_pf:.4f}s")

if __name__ == '__main__':
    run_benchmark()
