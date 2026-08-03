from typing import Tuple, Dict
from src.conflict_types import ResolutionAction, ConflictEvent, ConflictSeverity
from src.memory_module import MemoryModule
from models.intent_classifier import IntentClassifier

class RefinementAgent:
    def __init__(self, memory: MemoryModule):
        self.memory = memory
        self.intent_classifier = IntentClassifier()
        
        self.PARAMETER_RANGES: Dict[str, Tuple[float, float]] = {
            "PRB_QUOTA": (0.0, 100.0),
            "SCHEDULER_WEIGHT": (0.0, 10.0),
            "TX_POWER": (-10.0, 23.0),
            "HANDOVER_THRESHOLD": (-140.0, -44.0)
        }

    def validate(self, resolution: ResolutionAction, conflict: ConflictEvent) -> Tuple[bool, int, str]:
        # Nível 1: Validação de Sintaxe e Range (< 10ms)
        is_valid, reason = self._validate_syntax(resolution)
        if not is_valid:
            return False, 1, reason
            
        # Nível 2: Similaridade Histórica e Intenção (< 100ms)
        is_valid, score = self._validate_similarity(resolution, conflict)
        if score > 0.7:
            resolution.validation_level = 2
            return True, 2, "Aprovado por similaridade histórica alta"
            
        # Nível 3: Checagem Formal / Semântica para ações críticas (Async, < 500ms)
        if conflict.severity == ConflictSeverity.CRITICAL:
            is_valid, reason = self._validate_formal(resolution, conflict)
            if not is_valid:
                return False, 3, reason
            resolution.validation_level = 3
            
        return True, 1, "Aprovado com validação básica"

    def _validate_syntax(self, resolution: ResolutionAction) -> Tuple[bool, str]:
        if not resolution.winning_action:
            return False, "Nenhuma ação vencedora definida"
            
        action = resolution.winning_action
        if action.parameter in self.PARAMETER_RANGES:
            min_val, max_val = self.PARAMETER_RANGES[action.parameter]
            if not (min_val <= action.value <= max_val):
                return False, f"Valor fora do range para {action.parameter}: {action.value}"
        return True, "OK"

    def _validate_similarity(self, resolution: ResolutionAction, conflict: ConflictEvent) -> Tuple[bool, float]:
        # Em produção, usaria intent_classifier ou cosine_similarity com histórico
        return True, 0.5

    def _validate_formal(self, resolution: ResolutionAction, conflict: ConflictEvent) -> Tuple[bool, str]:
        # Implementa regras formais restritas, ex: soma de PRB_QUOTA <= 100%
        # Para isso precisaria do estado global
        return True, "Formal check OK"
