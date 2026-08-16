import torch
import torch.nn as nn
import numpy as np
from typing import Tuple, Dict, List, Optional
from src.conflict_types import ConflictEvent, XAppAction

class ActorNetwork(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Softmax(dim=-1)
        )
        
    def forward(self, obs):
        return self.net(obs)

class CriticNetwork(nn.Module):
    def __init__(self, global_obs_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(global_obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
        
    def forward(self, global_obs):
        return self.net(global_obs)

class MAPPOAgent:
    def __init__(self, obs_dim: int, action_dim: int, n_agents: int, lr=3e-4, gamma=0.99, clip_eps=0.2):
        self.actor = ActorNetwork(obs_dim, action_dim)
        self.critic = CriticNetwork(obs_dim * n_agents)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=lr)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=lr)
        self.gamma = gamma
        self.clip_eps = clip_eps
        
    def select_action(self, obs: np.ndarray) -> Tuple[int, float]:
        obs_tensor = torch.FloatTensor(obs).unsqueeze(0)
        with torch.no_grad():
            probs = self.actor(obs_tensor)
            dist = torch.distributions.Categorical(probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
        return action.item(), log_prob.item()
        
    def update(self, rollout_buffer: List[dict]) -> Dict[str, float]:
        # Placeholder for PPO update logic
        return {"actor_loss": 0.0, "critic_loss": 0.0}

class MAPPOCoordinator:
    def __init__(self, n_agents: int, obs_dim: int, action_dim: int, config: dict):
        # Baseado na "Espinha Dorsal Cognitiva MAPPO"
        # O estado (obs_dim) contém Rádio, Recursos, QoS, Mobilidade, Energia, Estado das xApps.
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.agents = [MAPPOAgent(obs_dim, action_dim, n_agents) for _ in range(n_agents)]
        
        # Pesos da Função de Recompensa (w1 a w5)
        self.w_T = config.get('weight_throughput', 1.0)
        self.w_L = config.get('weight_latency', 1.0)
        self.w_SLA = config.get('weight_sla_violation', 2.0)
        self.w_E = config.get('weight_energy', 1.0)
        self.w_O = config.get('weight_oscillation', 0.5)

    def compute_reward(self, throughput: float, latency: float, sla_violations: int, energy: float, oscillation: float) -> float:
        """
        Função de Recompensa baseada no documento "Espinha Dorsal Cognitiva"
        R = w1*T - w2*L - w3*SLA - w4*Energia - w5*Oscilação
        """
        return (self.w_T * throughput) - (self.w_L * latency) - (self.w_SLA * sla_violations) - (self.w_E * energy) - (self.w_O * oscillation)

    def _build_state_vector(self, kpm_state: Dict[str, float], conflict: ConflictEvent) -> np.ndarray:
        """
        Mapeia métricas para um vetor de observação.
        """
        state = np.zeros(self.obs_dim)
        if not kpm_state:
            return state
            
        # Exemplo de mapeamento para o Actor:
        # [0] = SINR
        # [1] = CQI
        # [2] = BLER
        # [3] = PRBs (prb_used_dl)
        # [4] = Throughput (drb_thp_dl)
        # [5] = Latência (drb_delay_dl)
        state[0] = kpm_state.get('sinr', 0.0)
        if self.obs_dim > 3:
            state[3] = kpm_state.get('prb_used_dl', 0.0)
        if self.obs_dim > 4:
            state[4] = kpm_state.get('drb_thp_dl', 0.0)
        if self.obs_dim > 5:
            state[5] = kpm_state.get('drb_delay_dl', 0.0)
        return state

    def decide(self, conflict: ConflictEvent, kpm_state: Optional[Dict[str, float]]) -> Tuple[Optional[XAppAction], float]:
        """
        Retorna a ação vencedora baseada no modelo MARL e a confiança da decisão.
        """
        if not conflict.involved_xapps:
            return None, 0.0
            
        # Constrói o estado (observação local/global)
        obs_vector = self._build_state_vector(kpm_state if kpm_state else {}, conflict)
        
        # Escolhe a ação usando o primeiro agente (em um cenário multi-agente real, cada xApp seria um agente)
        # Aqui simplificamos assumindo que o Coordenador usa o Agente PPO para decidir o conflito.
        action_idx, log_prob = self.agents[0].select_action(obs_vector)
        
        # Mapeia a ação da rede neural de volta para as opções possíveis no conflito
        safe_idx = action_idx % len(conflict.involved_xapps)
        winning_action = conflict.involved_xapps[safe_idx]
        
        # Calcula a confiança baseada na probabilidade logarítmica
        confidence = float(np.exp(log_prob))
        
        return winning_action, confidence
