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

print("Benchmarking overall results extraction inside run_power_flow()...")

start = time.time()
for _ in range(10):
    engine.run_power_flow()
end = time.time()

print(f"Time taken for 10 iterations of run_power_flow(): {end - start:.4f} seconds")
