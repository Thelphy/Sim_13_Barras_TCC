import pandapower as pp
import numpy as np

def generate_pv_curve(net, target_bus_idx, load_idx, base_p, base_q):
    v_results = []
    p_results = []

    factor = 1.0
    step = 0.1
    min_step = 1e-4

    while step >= min_step:
        net.load.loc[load_idx, 'p_mw'] = base_p * factor
        net.load.loc[load_idx, 'q_mvar'] = base_q * factor

        try:
            pp.runpp(net)
            v_pu = net.res_bus.loc[target_bus_idx, 'vm_pu']
            p_mw = net.load.loc[load_idx, 'p_mw']
            v_results.append(v_pu)
            p_results.append(p_mw)

            factor += step
        except pp.powerflow.LoadflowNotConverged:
            factor -= step
            step /= 2.0
            factor += step
        except Exception:
            factor -= step
            step /= 2.0
            factor += step

    # Restore
    net.load.loc[load_idx, 'p_mw'] = base_p
    net.load.loc[load_idx, 'q_mvar'] = base_q

    return p_results, v_results

net = pp.create_empty_network()
b1 = pp.create_bus(net, vn_kv=13.8, type="b")
b2 = pp.create_bus(net, vn_kv=13.8, type="b")
pp.create_ext_grid(net, bus=b1, vm_pu=1.0)
pp.create_line_from_parameters(net, from_bus=b1, to_bus=b2, length_km=10, r_ohm_per_km=0.1, x_ohm_per_km=0.1, c_nf_per_km=10, max_i_ka=1)
l1 = pp.create_load(net, bus=b2, p_mw=1.0, q_mvar=0.2)

pp.runpp(net)
p, v = generate_pv_curve(net, b2, l1, 1.0, 0.2)
print("Points:", len(p))
print("Last P:", p[-1], "Last V:", v[-1])
