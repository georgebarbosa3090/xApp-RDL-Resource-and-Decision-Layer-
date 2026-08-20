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
        self.agents = [MAPPOAgent(obs_dim, action_dim, n_agents) for _ in range(n_agents)]
        
    def decide(self, conflict: ConflictEvent, kpm_state: Optional[Dict[str, float]]) -> Tuple[Optional[XAppAction], float]:
        """
        Retorna a ação vencedora baseada no modelo MARL e a confiança da decisão.
        """
        if not conflict.involved_xapps:
            return None, 0.0
            
        # Mock de decisão simples para testes
        winning_action = conflict.involved_xapps[0]
        confidence = 0.85
        return winning_action, confidence
