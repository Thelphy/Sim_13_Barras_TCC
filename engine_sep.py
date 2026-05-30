import pandapower as pp
import numpy as np
from scipy.linalg import eig
from data_models import SystemState, SimulationResults

class PowerSystemEngine:
    def __init__(self):
        self.net = pp.create_empty_network()
        self.results = SimulationResults()

    def build_network(self, state: SystemState):
        self.net = pp.create_empty_network()

        # Mapping from our bus id to pandapower bus index
        self.bus_mapping = {}

        for bus_id, bus in state.buses.items():
            idx = pp.create_bus(self.net, name=bus.name, vn_kv=bus.vn_kv, type="b")
            self.bus_mapping[bus_id] = idx

            if bus.type == 'slack':
                pp.create_ext_grid(self.net, bus=idx, vm_pu=bus.v_target_pu, name=f"ExtGrid {bus.name}")
            elif bus.type == 'pv' and bus.gen_enabled:
                pp.create_gen(self.net, bus=idx, p_mw=bus.p_gen_kw/1000.0, vm_pu=bus.v_target_pu, name=f"Gen {bus.name}")

            # If it is a PQ bus but it has generation and generation is enabled
            if bus.type == 'pq' and bus.gen_enabled and bus.p_gen_kw > 0:
                pp.create_sgen(self.net, bus=idx, p_mw=bus.p_gen_kw/1000.0, name=f"SGen {bus.name}")

            # Add loads
            p_load_mw = bus.p_load_kw / 1000.0 if bus.p_load_enabled else 0.0
            q_load_mvar = bus.q_load_kvar / 1000.0 if bus.q_load_enabled else 0.0

            if p_load_mw != 0 or q_load_mvar != 0:
                pp.create_load(self.net, bus=idx, p_mw=p_load_mw, q_mvar=q_load_mvar, name=f"Load {bus.name}")

        for line_id, line in state.lines.items():
            from_idx = self.bus_mapping[line.from_bus]
            to_idx = self.bus_mapping[line.to_bus]
            if line.is_transformer:
                # We assume generic parameters for the transformer
                # Ensure hv_bus is the one with higher voltage
                vn_from = self.net.bus.at[from_idx, 'vn_kv']
                vn_to = self.net.bus.at[to_idx, 'vn_kv']

                if vn_from >= vn_to:
                    hv_bus = from_idx
                    lv_bus = to_idx
                    vn_hv_kv = vn_from
                    vn_lv_kv = vn_to
                else:
                    hv_bus = to_idx
                    lv_bus = from_idx
                    vn_hv_kv = vn_to
                    vn_lv_kv = vn_from

                # Specific parameters for 633-634 500 kVA transformer (4.16/0.48 kV)
                if vn_hv_kv == 4.16 and vn_lv_kv == 0.48:
                    sn_mva = 0.5
                    vk_percent = 2.0
                    vkr_percent = 0.5
                    pfe_kw = 1.0
                    i0_percent = 0.5
                else:
                    sn_mva = 5.0 # default sn_mva
                    vk_percent = 5.0
                    vkr_percent = 1.0
                    pfe_kw = 10.0
                    i0_percent = 0.5

                pp.create_transformer_from_parameters(self.net, hv_bus=hv_bus, lv_bus=lv_bus,
                                                      sn_mva=sn_mva, vn_hv_kv=vn_hv_kv, vn_lv_kv=vn_lv_kv,
                                                      vk_percent=vk_percent, vkr_percent=vkr_percent,
                                                      pfe_kw=pfe_kw, i0_percent=i0_percent,
                                                      name=f"Trafo {line_id}")
            else:
                pp.create_line_from_parameters(self.net, from_bus=from_idx, to_bus=to_idx,
                                               length_km=line.length_km,
                                               r_ohm_per_km=line.r_ohm_per_km,
                                               x_ohm_per_km=line.x_ohm_per_km,
                                               c_nf_per_km=line.c_nf_per_km,
                                               max_i_ka=line.max_i_ka,
                                               name=f"Line {line_id}")

    def run_power_flow(self):
        try:
            pp.runpp(self.net)
            self.results.success = True

            # Extract Bus Results
            bus_names = self.net.bus['name'].values
            vm_pus = self.net.res_bus['vm_pu'].values
            va_degs = self.net.res_bus['va_degree'].values
            p_mws = self.net.res_bus['p_mw'].values
            q_mvars = self.net.res_bus['q_mvar'].values

            bus_res = []
            for bus_name, v_pu, va_deg, p_mw, q_mvar in zip(bus_names, vm_pus, va_degs, p_mws, q_mvars):
                bus_res.append([bus_name, f"{v_pu:.4f}", f"{va_deg:.2f}", f"{p_mw:.2f}", f"{q_mvar:.2f}"])
            self.results.bus_results = bus_res

            # Extract Line Results
            line_names = self.net.line['name'].values
            p_from_mws = self.net.res_line['p_from_mw'].values
            q_from_mvars = self.net.res_line['q_from_mvar'].values
            p_to_mws = self.net.res_line['p_to_mw'].values
            q_to_mvars = self.net.res_line['q_to_mvar'].values
            pl_mws = self.net.res_line['pl_mw'].values
            loadings = self.net.res_line['loading_percent'].values

            line_res = []
            for line_name, p_from_mw, q_from_mvar, p_to_mw, q_to_mvar, pl_mw, loading in zip(line_names, p_from_mws, q_from_mvars, p_to_mws, q_to_mvars, pl_mws, loadings):
                line_res.append([line_name, f"{p_from_mw:.2f}", f"{q_from_mvar:.2f}", f"{p_to_mw:.2f}", f"{q_to_mvar:.2f}", f"{pl_mw:.4f}", f"{loading:.2f}"])

            # Extract Transformer Results (append to line_res)
            if not self.net.trafo.empty:
                trafo_names = self.net.trafo['name'].values
                p_from_mws_t = self.net.res_trafo['p_hv_mw'].values
                q_from_mvars_t = self.net.res_trafo['q_hv_mvar'].values
                p_to_mws_t = self.net.res_trafo['p_lv_mw'].values
                q_to_mvars_t = self.net.res_trafo['q_lv_mvar'].values
                pl_mws_t = self.net.res_trafo['pl_mw'].values
                loadings_t = self.net.res_trafo['loading_percent'].values

                for t_name, p_from_mw, q_from_mvar, p_to_mw, q_to_mvar, pl_mw, loading in zip(trafo_names, p_from_mws_t, q_from_mvars_t, p_to_mws_t, q_to_mvars_t, pl_mws_t, loadings_t):
                    line_res.append([t_name, f"{p_from_mw:.2f}", f"{q_from_mvar:.2f}", f"{p_to_mw:.2f}", f"{q_to_mvar:.2f}", f"{pl_mw:.4f}", f"{loading:.2f}"])

            self.results.line_results = line_res

        except pp.powerflow.LoadflowNotConverged:
            self.results.success = False
            print("Power flow failed: Loadflow did not converge.")
        except Exception:
            self.results.success = False
            print("Power flow failed: An unexpected error occurred.")

    def run_modal_analysis(self):
        # Modal Analysis using Newton-Raphson Jacobian (J_R)
        if not self.results.success:
            return

        try:
            ppc = self.net._ppc
            if 'J' not in ppc['internal']:
                return

            J = ppc['internal']['J'].toarray()

            from pandapower.pypower.bustypes import bustypes
            ref, pv, pq = bustypes(ppc['bus'], ppc['gen'])

            n_pq = len(pq)
            n_npv = len(pq) + len(pv)

            if n_pq > 0:
                # Submatrices of the full Jacobian J
                J11 = J[:n_npv, :n_npv]
                J12 = J[:n_npv, n_npv:]
                J21 = J[n_npv:, :n_npv]
                J22 = J[n_npv:, n_npv:]

                # Reduced Jacobian JR = J22 - J21 * inv(J11) * J12
                J11_inv = np.linalg.inv(J11)
                JR = J22 - J21.dot(J11_inv).dot(J12)

                eigenvalues, eigenvectors = eig(JR)
                real_eigenvalues = eigenvalues.real

                # Sort ascending
                idx_sort = np.argsort(real_eigenvalues)
                real_eigenvalues = real_eigenvalues[idx_sort]
                eigenvectors = eigenvectors[:, idx_sort]

                self.results.eigenvalues = real_eigenvalues.tolist()

                # Calculate participation factors for the smallest eigenvalue
                if len(real_eigenvalues) > 0:
                    min_eig_idx = 0
                    right_eigenvector = eigenvectors[:, min_eig_idx]

                    e0 = np.zeros(eigenvectors.shape[0])
                    e0[min_eig_idx] = 1.0
                    left_eigenvector = np.linalg.solve(eigenvectors.T, e0)

                    participation = np.abs(right_eigenvector * left_eigenvector)
                    # Normalize
                    if np.sum(participation) > 0:
                        participation = participation / np.sum(participation)

                    bus_lookup = self.net._pd2ppc_lookups["bus"]

                    part_factors = {}
                    for i, p in enumerate(participation):
                        ppc_bus_idx = pq[i]
                        net_bus_idx = np.where(bus_lookup == ppc_bus_idx)[0][0]
                        bus_name = self.net.bus.loc[net_bus_idx, 'name']
                        part_factors[bus_name] = p

                    self.results.participation_factors = part_factors
        except Exception:
            print("Modal analysis failed: An unexpected error occurred.")

    def generate_pv_curve(self, target_bus_name: str):
        if not self.results.success:
            return

        # Find bus index
        target_bus_idx = self.net.bus[self.net.bus.name == target_bus_name].index
        if len(target_bus_idx) == 0:
            return
        target_bus_idx = target_bus_idx[0]

        # Check if there is load at this bus
        load_idx = self.net.load[self.net.load.bus == target_bus_idx].index
        if len(load_idx) == 0:
            # Create a small base load to allow scaling
            created_load_idx = pp.create_load(self.net, bus=target_bus_idx, p_mw=0.01, q_mvar=0.0, name=f"Load {target_bus_name}")
            load_idx = [created_load_idx]
        load_idx = load_idx[0]

        base_p = self.net.load.loc[load_idx, 'p_mw']
        base_q = self.net.load.loc[load_idx, 'q_mvar']

        if base_p == 0:
            # Add a small base P to allow scaling
            base_p = 0.01

        p_factors = np.linspace(1.0, 5.0, 40)
        v_results = []
        p_results = []

        for factor in p_factors:
            self.net.load.loc[load_idx, 'p_mw'] = base_p * factor
            self.net.load.loc[load_idx, 'q_mvar'] = base_q * factor

            try:
                pp.runpp(self.net, init='flat')
                v_pu = self.net.res_bus.loc[target_bus_idx, 'vm_pu']
                p_mw = self.net.load.loc[load_idx, 'p_mw']
                v_results.append(v_pu)
                p_results.append(p_mw)
            except pp.powerflow.LoadflowNotConverged:
                break

        # Restore original load
        self.net.load.loc[load_idx, 'p_mw'] = base_p
        self.net.load.loc[load_idx, 'q_mvar'] = base_q

        self.results.pv_curve_p = p_results
        self.results.pv_curve_v = v_results
