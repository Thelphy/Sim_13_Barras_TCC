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
    try:
        pp.runpp(engine.net)
    except Exception as e:
        pass
    print(f"Power flow time: {time.time() - start_pf:.4f}s")

    # Benchmark Bus Results
    print("Benchmarking Bus Results iteration...")
    start_bus = time.time()
    bus_res = []
    for idx, row in engine.net.res_bus.iterrows():
        bus_name = engine.net.bus.loc[idx, 'name']
        v_pu = row['vm_pu']
        va_deg = row['va_degree']
        p_mw = row['p_mw']
        q_mvar = row['q_mvar']
        bus_res.append([bus_name, f"{v_pu:.4f}", f"{va_deg:.2f}", f"{p_mw:.2f}", f"{q_mvar:.2f}"])
    bus_time = time.time() - start_bus
    print(f"Bus iteration time: {bus_time:.4f}s")

    # Benchmark Line Results
    print("Benchmarking Line Results iteration...")
    start_line = time.time()
    line_res = []
    for idx, row in engine.net.res_line.iterrows():
        line_name = engine.net.line.loc[idx, 'name']
        p_from_mw = row['p_from_mw']
        q_from_mvar = row['q_from_mvar']
        p_to_mw = row['p_to_mw']
        q_to_mvar = row['q_to_mvar']
        pl_mw = row['pl_mw']
        ql_mvar = row['ql_mvar']
        loading = row['loading_percent']
        line_res.append([line_name, f"{p_from_mw:.2f}", f"{q_from_mvar:.2f}", f"{p_to_mw:.2f}", f"{q_to_mvar:.2f}", f"{pl_mw:.4f}", f"{loading:.2f}"])
    line_time = time.time() - start_line
    print(f"Line iteration time: {line_time:.4f}s")

    print(f"Total iteration time: {bus_time + line_time:.4f}s")

if __name__ == '__main__':
    run_benchmark()
