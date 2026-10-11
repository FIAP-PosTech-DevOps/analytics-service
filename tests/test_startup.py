"""Inicialização: variáveis obrigatórias, endpoint customizado e falhas do boto3."""
import importlib
import sys
from unittest import mock

import pytest
from botocore.exceptions import NoCredentialsError


def importar_app():
    sys.modules.pop("app", None)
    return importlib.import_module("app")


@pytest.mark.parametrize("variavel", ["AWS_REGION", "AWS_SQS_URL", "AWS_DYNAMODB_TABLE"])
def test_sem_variavel_obrigatoria_encerra(monkeypatch, variavel):
    monkeypatch.delenv(variavel)
    with mock.patch("boto3.Session"), mock.patch("threading.Thread"), pytest.raises(SystemExit) as saida:
        importar_app()
    assert saida.value.code == 1


def test_endpoint_customizado_e_repassado_aos_clientes(monkeypatch):
    # Uso local com LocalStack.
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localstack:4566")
    with mock.patch("boto3.Session") as session_cls, mock.patch("threading.Thread"):
        importar_app()
    chamadas = session_cls.return_value.client.call_args_list
    assert {c.kwargs["endpoint_url"] for c in chamadas} == {"http://localstack:4566"}


@pytest.mark.parametrize("erro", [NoCredentialsError(), RuntimeError("boto3 quebrado")])
def test_falha_ao_criar_clientes_encerra(erro):
    with mock.patch("boto3.Session", side_effect=erro), mock.patch("threading.Thread"), \
            pytest.raises(SystemExit) as saida:
        importar_app()
    assert saida.value.code == 1
