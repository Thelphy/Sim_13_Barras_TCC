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
            elif bus.type == 'pv':
                pp.create_gen(self.net, bus=idx, p_mw=bus.p_gen_kw/1000.0, vm_pu=bus.v_target_pu, name=f"Gen {bus.name}")

            # Add loads
            if bus.p_load_kw > 0 or bus.q_load_kvar > 0:
                pp.create_load(self.net, bus=idx, p_mw=bus.p_load_kw/1000.0, q_mvar=bus.q_load_kvar/1000.0, name=f"Load {bus.name}")

        for line_id, line in state.lines.items():
            from_idx = self.bus_mapping[line.from_bus]
            to_idx = self.bus_mapping[line.to_bus]
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
            bus_res = []
            for idx, row in self.net.res_bus.iterrows():
                bus_name = self.net.bus.loc[idx, 'name']
                v_pu = row['vm_pu']
                va_deg = row['va_degree']
                p_mw = row['p_mw']
                q_mvar = row['q_mvar']
                bus_res.append([bus_name, f"{v_pu:.4f}", f"{va_deg:.2f}", f"{p_mw:.2f}", f"{q_mvar:.2f}"])
            self.results.bus_results = bus_res

            # Extract Line Results
            line_res = []
            for idx, row in self.net.res_line.iterrows():
                line_name = self.net.line.loc[idx, 'name']
                p_from_mw = row['p_from_mw']
                q_from_mvar = row['q_from_mvar']
                p_to_mw = row['p_to_mw']
                q_to_mvar = row['q_to_mvar']
                pl_mw = row['pl_mw']
                ql_mvar = row['ql_mvar']
                loading = row['loading_percent']
                line_res.append([line_name, f"{p_from_mw:.2f}", f"{q_from_mvar:.2f}", f"{p_to_mw:.2f}", f"{q_to_mvar:.2f}", f"{pl_mw:.4f}", f"{loading:.2f}"])
            self.results.line_results = line_res

        except Exception as e:
            self.results.success = False
            print(f"Power flow failed: {e}")

    def run_modal_analysis(self):
        # Simplistic Modal Analysis using Newton-Raphson Jacobian (J_R)
        # Note: pandapower does not directly expose the full analytical Jacobian from newtonpf
        # This is a simplified approach or we can compute an approximate reduced Jacobian.
        if not self.results.success:
            return

        try:
            # We get Ybus from pandapower internal components
            Ybus = self.net._ppc['internal']['Ybus']

            # As a proxy for stability, we will just look at eigenvalues of the Ybus matrix's magnitude
            # A rigorous modal analysis requires dQ/dV reduced Jacobian (J_R).
            # For the sake of this code, we compute a simplified reduced Jacobian.

            pq_buses = self.net.bus[self.net.bus.type == 'b'].index
            n_pq = len(pq_buses)

            if n_pq > 0:
                # We can approximate J_R using imaginary part of Ybus for PQ buses
                # J_R ≈ -B_reduced (where B is susceptance)
                # This is a classic approximation in power systems.
                Y_reduced = Ybus[np.ix_(pq_buses, pq_buses)]
                B_reduced = Y_reduced.imag

                # J_R approx -B
                J_R = -B_reduced.toarray()

                eigenvalues, eigenvectors = eig(J_R)
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
                    left_eigenvector = np.linalg.inv(eigenvectors)[min_eig_idx, :]

                    participation = np.abs(right_eigenvector * left_eigenvector)
                    # Normalize
                    if np.sum(participation) > 0:
                        participation = participation / np.sum(participation)

                    self.results.participation_factors = {self.net.bus.loc[pq_buses[i], 'name']: p for i, p in enumerate(participation)}
        except Exception as e:
            print(f"Modal analysis failed: {e}")

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
            return
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
