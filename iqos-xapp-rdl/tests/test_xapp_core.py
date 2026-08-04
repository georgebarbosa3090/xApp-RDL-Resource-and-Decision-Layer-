import pytest
import json
from unittest.mock import MagicMock
from src.rdl_xapp import RDLxApp
from src.conflict_types import XAppAction

@pytest.fixture
def rdl_app():
    # Evita inicializar o loop de eventos real e socket RMR
    app = RDLxApp()
    app.xapp.rmr_send = MagicMock(return_value=True)
    app.xapp.rmr_free = MagicMock()
    app.metrics = MagicMock() # Desativa Prometheus real
    return app

def test_kpm_handler_decodes_and_updates_perception(rdl_app):
    # Simulando um payload APER que o decoder entenda
    # O mock atual aceita qualquer byte string e retorna um dicionário mockado
    summary = {"payload": b"fake_aper_payload"}
    sbuf = MagicMock()
    
    # Executa o handler
    rdl_app._kpm_indication_handler(rdl_app.xapp, summary, sbuf)
    
    # Verifica se a percepção atualizou (o mock reporta gnb_01 e drb_thp_dl=15.5)
    assert len(rdl_app.perception.kpm_state) > 0
    assert "gnb_01" in rdl_app.perception.kpm_state

def test_action_proposal_handler_resolves_conflict(rdl_app):
    # Cria duas propostas para o mesmo nó e parâmetro (Conflito Direto)
    payload1 = json.dumps({"xapp_id": "qos", "node_id": "gnb_01", "parameter": "PRB_QUOTA", "value": 80, "priority": 100}).encode()
    payload2 = json.dumps({"xapp_id": "energy", "node_id": "gnb_01", "parameter": "PRB_QUOTA", "value": 40, "priority": 60}).encode()
    
    sbuf = MagicMock()
    
    # Processa a primeira ação (não gera conflito isoladamente, mas é registrada)
    rdl_app._action_proposal_handler(rdl_app.xapp, {"payload": payload1}, sbuf)
    
    # Processa a segunda ação (gera conflito, resolve, refina, e envia RIC_CONTROL)
    rdl_app._action_proposal_handler(rdl_app.xapp, {"payload": payload2}, sbuf)
    
    # O rmr_send deve ter sido chamado para o RIC_CONTROL_REQ (mtype=12010)
    # com os dados da QoS xApp (prioridade 100 vence)
    assert rdl_app.xapp.rmr_send.called
    call_args = rdl_app.xapp.rmr_send.call_args[1]
    
    assert call_args["mtype"] == 12010
    sent_payload = json.loads(call_args["payload"].decode())
    assert sent_payload["parameter"] == "PRB_QUOTA"
    assert sent_payload["value"] == 80  # A prioridade maior venceu
