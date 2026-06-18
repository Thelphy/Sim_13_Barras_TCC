import pandapower as pp
import numpy as np
from data_models import SystemState, SimulationResults

# Classe principal que processa os cálculos da simulação elétrica do sistema
class PowerSystemEngine:
    # Inicializa a engine, criando a rede vazia e os objetos de resultado
    def __init__(self):
        self.net = pp.create_empty_network()
        self.results = SimulationResults()

    # Função responsável por construir a rede no Pandapower a partir do SystemState
    def build_network(self, state: SystemState):
        """Constrói a rede elétrica no pandapower com base no estado do sistema."""
        self.net = pp.create_empty_network()

        # Mapeamento do nosso id de barra para o índice de barra do pandapower
        self.bus_mapping = {}

        for bus_id, bus in state.buses.items():
            idx = pp.create_bus(self.net, name=bus.name, vn_kv=bus.vn_kv, type="b")
            self.bus_mapping[bus_id] = idx

            if bus.type == 'slack':
                pp.create_ext_grid(self.net, bus=idx, vm_pu=bus.v_target_pu, name=f"ExtGrid {bus.name}")
            elif bus.type == 'pv' and bus.gen_enabled:
                pp.create_gen(self.net, bus=idx, p_mw=bus.p_gen_kw/1000.0, vm_pu=bus.v_target_pu, name=f"Gen {bus.name}")

            # Se for uma barra PQ mas tiver geração e a geração estiver habilitada
            if bus.type == 'pq' and bus.gen_enabled and bus.p_gen_kw > 0:
                pp.create_sgen(self.net, bus=idx, p_mw=bus.p_gen_kw/1000.0, name=f"SGen {bus.name}")

            # Adicionar cargas
            p_load_mw = bus.p_load_kw / 1000.0 if bus.p_load_enabled else 0.0
            q_load_mvar = bus.q_load_kvar / 1000.0 if bus.q_load_enabled else 0.0

            if p_load_mw != 0 or q_load_mvar != 0:
                pp.create_load(self.net, bus=idx, p_mw=p_load_mw, q_mvar=q_load_mvar, name=f"Load {bus.name}")

        for line_id, line in state.lines.items():
            from_idx = self.bus_mapping[line.from_bus]
            to_idx = self.bus_mapping[line.to_bus]
            if line.is_transformer:
                # Assumimos parâmetros genéricos para o transformador
                # Garante que hv_bus seja o de maior tensão
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

                sn_mva = line.sn_mva
                vk_percent = line.vk_percent
                vkr_percent = line.vkr_percent
                pfe_kw = line.pfe_kw
                i0_percent = line.i0_percent

                pp.create_transformer_from_parameters(self.net, hv_bus=hv_bus, lv_bus=lv_bus,
                                                      sn_mva=sn_mva, vn_hv_kv=vn_hv_kv, vn_lv_kv=vn_lv_kv,
                                                      vk_percent=vk_percent, vkr_percent=vkr_percent,
                                                      pfe_kw=pfe_kw, i0_percent=i0_percent,
                                                      name=f"Trafo {line_id}")
            else:
                r_eff = max(line.r_ohm_per_km, 0.01)
                x_eff = max(line.x_ohm_per_km, 0.01)
                len_eff = max(line.length_km, 0.01)

                pp.create_line_from_parameters(self.net, from_bus=from_idx, to_bus=to_idx,
                                               length_km=len_eff,
                                               r_ohm_per_km=r_eff,
                                               x_ohm_per_km=x_eff,
                                               c_nf_per_km=line.c_nf_per_km,
                                               max_i_ka=line.max_i_ka,
                                               name=f"Line {line_id}")

    # Função que roda o fluxo de potência e armazena os resultados na classe
    def run_power_flow(self):
        """Executa o fluxo de potência e extrai os resultados para a UI."""
        try:
            pp.runpp(self.net, numba=False)
            self.results.success = True

            # Extrair Resultados das Barras
            bus_names = self.net.bus['name'].values
            vm_pus = self.net.res_bus['vm_pu'].values
            va_degs = self.net.res_bus['va_degree'].values
            p_mws = self.net.res_bus['p_mw'].values
            q_mvars = self.net.res_bus['q_mvar'].values

            bus_res = []
            for bus_name, v_pu, va_deg, p_mw, q_mvar in zip(bus_names, vm_pus, va_degs, p_mws, q_mvars):
                bus_res.append([bus_name, f"{v_pu:.4f}", f"{va_deg:.2f}", f"{p_mw:.2f}", f"{q_mvar:.2f}"])
            self.results.bus_results = bus_res

            # Extrair Resultados das Linhas
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

            # Extrair Resultados dos Transformadores (anexar a line_res)
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

    # Função que calcula e extrai os dados para a curva PV da barra solicitada
    def generate_pv_curve(self, target_bus_name: str):
        """Gera a Curva PV para uma barra alvo específica."""
        if not self.results.success:
            return

        import copy

        # Encontrar índice da barra
        target_bus_idx = self.net.bus[self.net.bus.name == target_bus_name].index
        if len(target_bus_idx) == 0:
            return
        target_bus_idx = target_bus_idx[0]

        # Verificar se há carga nesta barra
        load_idx = self.net.load[self.net.load.bus == target_bus_idx].index
        if len(load_idx) == 0:
            # Criar uma pequena carga base para permitir o escalonamento
            created_load_idx = pp.create_load(self.net, bus=target_bus_idx, p_mw=0.01, q_mvar=0.0, name=f"Load {target_bus_name}")
            load_idx = [created_load_idx]
        load_idx = load_idx[0]

        base_p = self.net.load.loc[load_idx, 'p_mw']
        base_q = self.net.load.loc[load_idx, 'q_mvar']

        if base_p < 0.01:
            base_p = 1.0 # Tratar carga 0 como base de 1 MW para escalonamento
            base_q = 0.0
            
        target_step_mw = 0.1
        step = target_step_mw / base_p
        min_step = 0.001 / base_p
        max_step = 15.0 / base_p  # Limitar o passo máximo a 15000 kW para uma curva mais suave

        v_results = []
        p_results = []

        factor = 0.0
        success_count = 0

        # 1. Traçar Curva Superior
        while step >= min_step:
            current_p = base_p * factor
            current_q = base_q * factor

            self.net.load.loc[load_idx, 'p_mw'] = current_p
            self.net.load.loc[load_idx, 'q_mvar'] = current_q

            try:
                pp.runpp(self.net, enforce_q_lims=False, numba=False)
                v_pu = self.net.res_bus.loc[target_bus_idx, 'vm_pu']
                p_mw = self.net.load.loc[load_idx, 'p_mw']
                v_results.append(v_pu)
                p_results.append(p_mw)
                factor += step
                success_count += 1
                if success_count >= 3:
                    step = min(step * 1.5, max_step)
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

        if len(v_results) > 0:
            v_nose = v_results[-1]
            
            # Restaurar para o último ponto de sucesso da curva superior para estabelecer o nariz exatamente
            last_success_factor = p_results[-1] / base_p
            self.net.load.loc[load_idx, 'p_mw'] = base_p * last_success_factor
            self.net.load.loc[load_idx, 'q_mvar'] = base_q * last_success_factor
            pp.runpp(self.net, enforce_q_lims=False, numba=False)
            
            # 2. Traçar Curva Inferior
            # Empurrar tensões para baixo para a bacia de atração inferior
            self.net.res_bus['vm_pu'] *= 0.85 
            
            # Manter as tensões das barras slack/PV fixas em seus setpoints
            for idx in self.net.ext_grid.bus.values:
                self.net.res_bus.loc[idx, 'vm_pu'] = self.net.ext_grid[self.net.ext_grid.bus == idx]['vm_pu'].values[0]
            for idx in self.net.gen.bus.values:
                self.net.res_bus.loc[idx, 'vm_pu'] = self.net.gen[self.net.gen.bus == idx]['vm_pu'].values[0]

            step_lower = -step
            factor_lower = last_success_factor + step_lower 
            min_step_lower = min_step
            
            p_lower = []
            v_lower = []
            
            last_good_res_bus = self.net.res_bus.copy()
            success_count_lower = 0

            while factor_lower >= 0:
                current_p = base_p * factor_lower
                current_q = base_q * factor_lower
                
                self.net.load.loc[load_idx, 'p_mw'] = current_p
                self.net.load.loc[load_idx, 'q_mvar'] = current_q
                
                try:
                    pp.runpp(self.net, enforce_q_lims=False, init="results", numba=False)
                    v_pu = self.net.res_bus.loc[target_bus_idx, 'vm_pu']
                    p_mw = self.net.load.loc[load_idx, 'p_mw']
                    
                    if v_pu >= v_nose:
                        # Saltou de volta para a curva superior, tratar como não-convergência
                        raise pp.powerflow.LoadflowNotConverged("Jumped to upper curve")
                        
                    v_lower.append(v_pu)
                    p_lower.append(p_mw)
                    last_good_res_bus = self.net.res_bus.copy()
                    factor_lower += step_lower
                    success_count_lower += 1
                    if success_count_lower >= 3:
                        step_lower = max(step_lower * 1.5, -max_step)
                except pp.powerflow.LoadflowNotConverged:
                    self.net.res_bus = last_good_res_bus.copy()
                    factor_lower -= step_lower
                    step_lower /= 2.5
                    factor_lower += step_lower
                    success_count_lower = 0
                    if abs(step_lower) < min_step_lower:
                        break
                except Exception:
                    self.net.res_bus = last_good_res_bus.copy()
                    factor_lower -= step_lower
                    step_lower /= 2.5
                    factor_lower += step_lower
                    success_count_lower = 0
                    if abs(step_lower) < min_step_lower:
                        break

            # Anexar os pontos da curva inferior aos resultados
            p_results.extend(p_lower)
            v_results.extend(v_lower)

        # Restaurar carga original
        self.net.load.loc[load_idx, 'p_mw'] = base_p
        self.net.load.loc[load_idx, 'q_mvar'] = base_q

        self.results.pv_curve_p = p_results
        self.results.pv_curve_v = v_results
