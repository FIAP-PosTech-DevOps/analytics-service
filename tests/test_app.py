"""Testes unitários do analytics-service (sem AWS real)."""
import json

from botocore.exceptions import ClientError


def mensagem(body):
    return {"MessageId": "m-1", "ReceiptHandle": "rh-1", "Body": body}


EVENTO = {
    "user_id": "u-42",
    "flag_name": "novo-checkout",
    "result": True,
    "timestamp": "2026-10-01T12:00:00Z",
}


def test_health(svc):
    resp = svc.client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_worker_do_sqs_sobe_em_background(svc):
    svc.thread_cls.assert_called_once()
    assert svc.thread_cls.call_args.kwargs["daemon"] is True
    svc.thread_cls.return_value.start.assert_called_once()


def test_evento_valido_vai_para_o_dynamodb_e_sai_da_fila(svc):
    svc.module.process_message(mensagem(json.dumps(EVENTO)))

    svc.dynamodb.put_item.assert_called_once()
    item = svc.dynamodb.put_item.call_args.kwargs["Item"]
    assert item["flag_name"] == {"S": "novo-checkout"}
    assert item["result"] == {"BOOL": True}
    svc.sqs.delete_message.assert_called_once()


def test_json_invalido_nao_e_apagado_da_fila(svc):
    # Fica na fila; depois de N tentativas a DLQ recebe a mensagem.
    svc.module.process_message(mensagem("isto não é json"))
    svc.dynamodb.put_item.assert_not_called()
    svc.sqs.delete_message.assert_not_called()


def test_erro_no_dynamodb_mantem_a_mensagem_na_fila(svc):
    svc.dynamodb.put_item.side_effect = ClientError(
        {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "lento"}}, "PutItem"
    )
    svc.module.process_message(mensagem(json.dumps(EVENTO)))
    svc.sqs.delete_message.assert_not_called()
