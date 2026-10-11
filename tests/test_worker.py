"""Loop do worker do SQS e caminhos de erro do processamento."""
import json
from unittest import mock

import pytest
from botocore.exceptions import ClientError


class Parar(BaseException):
    """Interrompe o loop infinito do worker no teste (não é pega por 'except Exception')."""


def erro_aws(codigo):
    return ClientError({"Error": {"Code": codigo, "Message": "falha"}}, "ReceiveMessage")


def test_evento_sem_campo_obrigatorio_fica_na_fila(svc):
    msg = {"MessageId": "m-2", "ReceiptHandle": "rh-2", "Body": json.dumps({"user_id": "u-1"})}
    svc.module.process_message(msg)
    svc.dynamodb.put_item.assert_not_called()
    svc.sqs.delete_message.assert_not_called()


def test_loop_processa_mensagens_e_se_recupera_de_erros(svc):
    evento = {"user_id": "u-1", "flag_name": "f", "result": False, "timestamp": "2026-10-01T00:00:00Z"}
    msg = {"MessageId": "m-1", "ReceiptHandle": "rh-1", "Body": json.dumps(evento)}
    svc.sqs.receive_message.side_effect = [
        {},                       # long polling sem mensagens
        {"Messages": [msg]},      # um lote com uma mensagem
        erro_aws("Throttling"),   # erro da AWS: espera e tenta de novo
        RuntimeError("rede"),     # erro inesperado: espera e tenta de novo
        Parar(),
    ]
    with mock.patch.object(svc.module.time, "sleep") as dormir, pytest.raises(Parar):
        svc.module.sqs_worker_loop()

    assert svc.sqs.receive_message.call_count == 5
    svc.dynamodb.put_item.assert_called_once()
    svc.sqs.delete_message.assert_called_once()
    assert dormir.call_count == 2
