"""Fixtures dos testes unitários.

O app.py cria os clientes da AWS e dispara o worker do SQS no momento do
import. Aqui o boto3 e a thread do worker são trocados por mocks ANTES do
import, então os testes rodam sem AWS, sem fila e sem DynamoDB.
"""
import importlib
import os
import sys
from unittest import mock

import pytest

os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_SQS_URL", "https://sqs.us-east-1.amazonaws.com/000000000000/fila-teste")
os.environ.setdefault("AWS_DYNAMODB_TABLE", "ToggleMasterAnalytics")


@pytest.fixture
def svc():
    with mock.patch("boto3.Session") as session_cls, mock.patch("threading.Thread") as thread_cls:
        clients = {"sqs": mock.Mock(name="sqs"), "dynamodb": mock.Mock(name="dynamodb")}
        session_cls.return_value.client.side_effect = lambda name, **_: clients[name]

        sys.modules.pop("app", None)
        module = importlib.import_module("app")
        module.app.config["TESTING"] = True

        yield mock.Mock(
            module=module,
            client=module.app.test_client(),
            sqs=clients["sqs"],
            dynamodb=clients["dynamodb"],
            thread_cls=thread_cls,
        )
