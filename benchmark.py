import time
import pandapower as pp
from engine_sep import PowerSystemEngine
from data_models import SystemState, BusData, LineData

def create_large_network():
    state = SystemState()
    # Create 1000 buses
    for i in range(1000):
        bus_type = "slack" if i == 0 else "pq"
        state.buses[i] = BusData(id=i, name=f"Bus {i}", type=bus_type, vn_kv=110.0,
                                      v_target_pu=1.0, p_load_kw=100.0, q_load_kvar=50.0)

    # Create lines to connect them in a chain
    for i in range(999):
        state.lines[i] = LineData(id=i, from_bus=i, to_bus=i+1,
                                        length_km=1.0, r_ohm_per_km=0.1, x_ohm_per_km=0.1,
                                        c_nf_per_km=10.0, max_i_ka=1.0)
    return state

engine = PowerSystemEngine()
state = create_large_network()
print("Building network...")
engine.build_network(state)

# Warmup run
print("Running power flow...")
engine.run_power_flow()

print("Benchmarking result extraction...")
# Isolate extraction step
def extract_results(engine):
    bus_res = []
    for idx, row in engine.net.res_bus.iterrows():
        bus_name = engine.net.bus.loc[idx, 'name']
        v_pu = row['vm_pu']
        va_deg = row['va_degree']
        p_mw = row['p_mw']
        q_mvar = row['q_mvar']
        bus_res.append([bus_name, f"{v_pu:.4f}", f"{va_deg:.2f}", f"{p_mw:.2f}", f"{q_mvar:.2f}"])

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
    return bus_res, line_res

start = time.time()
for _ in range(10):
    extract_results(engine)
end = time.time()

print(f"Time taken for 10 iterations: {end - start:.4f} seconds")

# Verify optimized version
def extract_results_optimized(engine):
    # Optimizing bus results
    bus_names = engine.net.bus['name'].values
    vm_pus = engine.net.res_bus['vm_pu'].values
    va_degs = engine.net.res_bus['va_degree'].values
    p_mws = engine.net.res_bus['p_mw'].values
    q_mvars = engine.net.res_bus['q_mvar'].values

    bus_res = []
    for bus_name, v_pu, va_deg, p_mw, q_mvar in zip(bus_names, vm_pus, va_degs, p_mws, q_mvars):
        bus_res.append([bus_name, f"{v_pu:.4f}", f"{va_deg:.2f}", f"{p_mw:.2f}", f"{q_mvar:.2f}"])

    # Optimizing line results
    line_names = engine.net.line['name'].values
    p_from_mws = engine.net.res_line['p_from_mw'].values
    q_from_mvars = engine.net.res_line['q_from_mvar'].values
    p_to_mws = engine.net.res_line['p_to_mw'].values
    q_to_mvars = engine.net.res_line['q_to_mvar'].values
    pl_mws = engine.net.res_line['pl_mw'].values
    loadings = engine.net.res_line['loading_percent'].values

    line_res = []
    for line_name, p_from_mw, q_from_mvar, p_to_mw, q_to_mvar, pl_mw, loading in zip(line_names, p_from_mws, q_from_mvars, p_to_mws, q_to_mvars, pl_mws, loadings):
         line_res.append([line_name, f"{p_from_mw:.2f}", f"{q_from_mvar:.2f}", f"{p_to_mw:.2f}", f"{q_to_mvar:.2f}", f"{pl_mw:.4f}", f"{loading:.2f}"])

    return bus_res, line_res

start2 = time.time()
for _ in range(10):
    extract_results_optimized(engine)
end2 = time.time()

print(f"Time taken for 10 iterations (optimized): {end2 - start2:.4f} seconds")

# Assert both methods give exactly the same result
orig_bus, orig_line = extract_results(engine)
opt_bus, opt_line = extract_results_optimized(engine)

assert orig_bus == opt_bus, "Bus results mismatch!"
assert orig_line == opt_line, "Line results mismatch!"

print("Results match! Optimization is valid.")
