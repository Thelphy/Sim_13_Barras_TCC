import sys
import time
from main import MainController
from engine_sep import PowerSystemEngine
import pandapower as pp

controller = MainController()
engine = PowerSystemEngine()
engine.build_network(controller.state)
engine.run_power_flow()

def test_pv_curve(bus_id):
    print(f"Starting PV curve for {bus_id}...")
    start = time.time()
    
    target_bus_name = bus_id
    target_bus_idx = engine.net.bus[engine.net.bus.name == target_bus_name].index[0]
    load_idx = engine.net.load[engine.net.load.bus == target_bus_idx].index
    if len(load_idx) == 0:
        created_load_idx = pp.create_load(engine.net, bus=target_bus_idx, p_mw=0.01, q_mvar=0.0, name=f"Load {target_bus_name}")
        load_idx = [created_load_idx]
    load_idx = load_idx[0]

    base_p = engine.net.load.loc[load_idx, 'p_mw']
    base_q = engine.net.load.loc[load_idx, 'q_mvar']

    if base_p < 0.01:
        base_p = 1.0 # 1 MW base
        base_q = 0.0 # unity PF
        
    target_step_mw = 0.1
    step = target_step_mw / base_p
    min_step = 0.001 / base_p # 1 kW precision

    v_results = []
    p_results = []
    factor = 0.0
    
    iters = 0
    success_count = 0

    while step >= min_step:
        iters += 1
        current_p = base_p * factor
        current_q = base_q * factor

        engine.net.load.loc[load_idx, 'p_mw'] = current_p
        engine.net.load.loc[load_idx, 'q_mvar'] = current_q

        try:
            pp.runpp(engine.net, enforce_q_lims=False, numba=False)
            v_pu = engine.net.res_bus.loc[target_bus_idx, 'vm_pu']
            p_mw = engine.net.load.loc[load_idx, 'p_mw']
            v_results.append(v_pu)
            p_results.append(p_mw)
            factor += step
            success_count += 1
            if success_count >= 3:
                step *= 1.5
        except pp.powerflow.LoadflowNotConverged:
            factor -= step
            step /= 2.5
            factor += step
            success_count = 0
        except Exception:
            factor -= step
            step /= 2.5
            factor += step
            success_count = 0
            
        if iters > 1000:
            print("INFINITE LOOP!")
            break

    print(f"Upper curve done in {time.time()-start:.2f} seconds. Max factor: {factor}, Points: {len(v_results)}")

test_pv_curve('632')
test_pv_curve('692')
