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

    bus_names = engine.net.bus['name'].values
    vm_pu = engine.net.res_bus['vm_pu'].values
    va_degree = engine.net.res_bus['va_degree'].values
    p_mw = engine.net.res_bus['p_mw'].values
    q_mvar = engine.net.res_bus['q_mvar'].values

    bus_res = [[str(name), f"{v:.4f}", f"{va:.2f}", f"{p:.2f}", f"{q:.2f}"]
               for name, v, va, p, q in zip(bus_names, vm_pu, va_degree, p_mw, q_mvar)]

    bus_time = time.time() - start_bus
    print(f"Bus iteration time: {bus_time:.4f}s")

    # Benchmark Line Results
    print("Benchmarking Line Results iteration...")
    start_line = time.time()

    line_names = engine.net.line['name'].values
    p_from = engine.net.res_line['p_from_mw'].values
    q_from = engine.net.res_line['q_from_mvar'].values
    p_to = engine.net.res_line['p_to_mw'].values
    q_to = engine.net.res_line['q_to_mvar'].values
    pl = engine.net.res_line['pl_mw'].values
    loading = engine.net.res_line['loading_percent'].values

    line_res = [[str(name), f"{pf:.2f}", f"{qf:.2f}", f"{pt:.2f}", f"{qt:.2f}", f"{pl_v:.4f}", f"{load:.2f}"]
                for name, pf, qf, pt, qt, pl_v, load in zip(line_names, p_from, q_from, p_to, q_to, pl, loading)]

    line_time = time.time() - start_line
    print(f"Line iteration time: {line_time:.4f}s")

    print(f"Total iteration time: {bus_time + line_time:.4f}s")

if __name__ == '__main__':
    run_benchmark()
