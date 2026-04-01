"""
apps/core/tests.py
Testes para o app core.
Cobre: validators (senha, e-mail, idade), utils, exceções e permissões.
"""

from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.core.exceptions import PermissaoNegadaException
from apps.core.utils import (
    gerar_token_verificacao,
    obter_dados_publicos_usuario,
    processar_solicitacao_amizade,
)
from apps.core.validators import (
    EmailValidator,
    IdadeMinimaValidator,
    validar_senha_segura,
)

Usuario = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
#  SENHA
# ──────────────────────────────────────────────────────────────────────────────


class ValidacaoSenhaTests(TestCase):
    """Testa a validacao de senhas via validar_senha_segura()."""

    def test_senha_muito_curta(self):
        valida, erros = validar_senha_segura("Ab1!")
        self.assertFalse(valida)
        self.assertTrue(any("minimo" in e.lower() or "8" in e for e in erros))

    def test_senha_sem_maiuscula(self):
        valida, erros = validar_senha_segura("senha123!@#")
        self.assertFalse(valida)
        self.assertTrue(any("maiuscula" in e.lower() for e in erros))

    def test_senha_sem_minuscula(self):
        valida, erros = validar_senha_segura("SENHA123!@#")
        self.assertFalse(valida)
        self.assertTrue(any("minuscula" in e.lower() for e in erros))

    def test_senha_sem_numero(self):
        valida, erros = validar_senha_segura("SenhaForte!@#")
        self.assertFalse(valida)
        self.assertTrue(any("numero" in e.lower() for e in erros))

    def test_senha_sem_especial(self):
        valida, erros = validar_senha_segura("SenhaForte123")
        self.assertFalse(valida)
        self.assertTrue(any("especial" in e.lower() for e in erros))

    def test_senha_forte(self):
        valida, erros = validar_senha_segura("SenhaForte123!@#")
        self.assertTrue(valida)
        self.assertEqual(erros, [])

    def test_senha_vazia(self):
        valida, erros = validar_senha_segura("")
        self.assertFalse(valida)
        self.assertTrue(len(erros) > 0)


# ──────────────────────────────────────────────────────────────────────────────
#  E-MAIL
# ──────────────────────────────────────────────────────────────────────────────


class ValidacaoEmailTests(TestCase):
    """Testa o EmailValidator."""

    def setUp(self):
        self.validator = EmailValidator()

    def test_formato_invalido_sem_arroba(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator("emailsemarroba.com")
        self.assertEqual(ctx.exception.code, "email_formato_invalido")

    def test_formato_invalido_sem_dominio(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator("usuario@")
        self.assertEqual(ctx.exception.code, "email_formato_invalido")

    def test_email_temporario_bloqueado(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator("teste@mailinator.com")
        self.assertEqual(ctx.exception.code, "email_temporario")

    def test_email_temporario_yopmail(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator("outro@yopmail.com")
        self.assertEqual(ctx.exception.code, "email_temporario")

    @patch("apps.core.validators._dominio_existe_no_dns", return_value=False)
    def test_dominio_inexistente(self, mock_dns):
        with self.assertRaises(ValidationError) as ctx:
            self.validator("usuario@dominioquenatexiste123456789.com")
        self.assertEqual(ctx.exception.code, "email_dominio_invalido")

    @patch("apps.core.validators._dominio_existe_no_dns", return_value=True)
    def test_email_valido(self, mock_dns):
        # Nao deve lancar excecao
        try:
            self.validator("usuario@gmail.com")
        except ValidationError:
            self.fail("EmailValidator levantou ValidationError para e-mail valido.")

    def test_email_normalizado_para_lowercase(self):
        """O validator nao deve falhar com letras maiusculas."""
        with patch("apps.core.validators._dominio_existe_no_dns", return_value=True):
            try:
                self.validator("Usuario@Gmail.COM")
            except ValidationError:
                self.fail("EmailValidator falhou para e-mail com maiusculas.")


# ──────────────────────────────────────────────────────────────────────────────
#  IDADE MÍNIMA
# ──────────────────────────────────────────────────────────────────────────────


class ValidacaoIdadeTests(TestCase):
    """Testa o IdadeMinimaValidator."""

    def setUp(self):
        self.validator = IdadeMinimaValidator(18)

    def test_menor_de_idade_bloqueado(self):
        menor = date.today() - timedelta(days=17 * 365)
        with self.assertRaises(ValidationError) as ctx:
            self.validator(menor)
        self.assertEqual(ctx.exception.code, "idade_minima")

    def test_exatamente_18_anos_hoje(self):
        hoje = date.today()
        dezoito_anos_atras = hoje.replace(year=hoje.year - 18)
        try:
            self.validator(dezoito_anos_atras)
        except ValidationError:
            self.fail("IdadeMinimaValidator bloqueou usuario com exatamente 18 anos.")

    def test_maior_de_idade_permitido(self):
        adulto = date.today() - timedelta(days=25 * 365)
        try:
            self.validator(adulto)
        except ValidationError:
            self.fail("IdadeMinimaValidator bloqueou adulto valido.")

    def test_aniversario_29_fevereiro(self):
        """Nao deve crashar com nascidos em 29/02."""
        try:
            nascimento_bissexto = date(2000, 2, 29)
            self.validator(nascimento_bissexto)
        except ValueError:
            self.fail("IdadeMinimaValidator crashou com 29/02.")

    def test_input_invalido(self):
        with self.assertRaises(ValidationError):
            self.validator("nao-e-uma-data")


# ──────────────────────────────────────────────────────────────────────────────
#  TOKEN DE VERIFICAÇÃO
# ──────────────────────────────────────────────────────────────────────────────


class GerarTokenVerificacaoTests(TestCase):
    """Testa a geracao de tokens JWT de verificacao."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="token@exemplo.com",
            password="Teste123!@#",  # nosec
            nome_completo="Usuario Token",
        )

    def test_gera_token_string(self):
        token = gerar_token_verificacao(self.usuario)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_token_tem_formato_jwt(self):
        """JWT tem exatamente 3 partes separadas por ponto."""
        token = gerar_token_verificacao(self.usuario)
        partes = token.split(".")
        self.assertEqual(len(partes), 3)

    def test_tokens_diferentes_por_usuario(self):
        outro = Usuario.objects.create_user(
            email="outro@exemplo.com",
            password="Teste123!@#",  # nosec
            nome_completo="Outro Usuario",
        )
        token1 = gerar_token_verificacao(self.usuario)
        token2 = gerar_token_verificacao(outro)
        self.assertNotEqual(token1, token2)


# ──────────────────────────────────────────────────────────────────────────────
#  DADOS PÚBLICOS DO USUÁRIO
# ──────────────────────────────────────────────────────────────────────────────


class ObterDadosPublicosTests(TestCase):
    """Testa a extracao de dados publicos do usuario."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="publico@exemplo.com",
            password="Teste123!@#",  # nosec
            nome_completo="Joao da Silva",
            pais_residencia="Brasil",
            cidade_residencia="Sao Paulo",
            biografia="Mochileiro apaixonado",
        )

    def test_retorna_campos_esperados(self):
        dados = obter_dados_publicos_usuario(self.usuario)
        for campo in ("uuid", "nome_completo", "pais_residencia", "cidade_residencia"):
            self.assertIn(campo, dados)

    def test_nao_expoe_email(self):
        dados = obter_dados_publicos_usuario(self.usuario)
        self.assertNotIn("email", dados)

    def test_nao_expoe_senha(self):
        dados = obter_dados_publicos_usuario(self.usuario)
        self.assertNotIn("password", dados)
        self.assertNotIn("senha", dados)

    def test_uuid_e_string(self):
        dados = obter_dados_publicos_usuario(self.usuario)
        self.assertIsInstance(dados["uuid"], str)


# ──────────────────────────────────────────────────────────────────────────────
#  SOLICITAÇÃO DE AMIZADE
# ──────────────────────────────────────────────────────────────────────────────


class ProcessarSolicitacaoAmizadeTests(TestCase):
    """Testa a logica de processar solicitacoes de amizade."""

    def setUp(self):
        self.usuario1 = Usuario.objects.create_user(
            email="usuario1@exemplo.com",
            password="Teste123!@#",  # nosec
            nome_completo="Usuario Um",
            email_verificado=True,
        )
        self.usuario2 = Usuario.objects.create_user(
            email="usuario2@exemplo.com",
            password="Teste123!@#",  # nosec
            nome_completo="Usuario Dois",
            email_verificado=True,
        )

    def test_nao_pode_enviar_para_si_mesmo(self):
        sucesso, erro = processar_solicitacao_amizade(
            remetente=self.usuario1,
            destinatario=self.usuario1,
        )
        self.assertFalse(sucesso)
        self.assertIsNotNone(erro)

    def test_requer_email_verificado(self):
        nao_verificado = Usuario.objects.create_user(
            email="nv@exemplo.com",
            password="Teste123!@#",  # nosec
            nome_completo="Nao Verificado",
            email_verificado=False,
        )
        sucesso, erro = processar_solicitacao_amizade(
            remetente=nao_verificado,
            destinatario=self.usuario2,
        )
        self.assertFalse(sucesso)
        self.assertIn("e-mail", erro.lower())

    def test_solicitacao_duplicada_bloqueada(self):
        processar_solicitacao_amizade(self.usuario1, self.usuario2)
        sucesso, erro = processar_solicitacao_amizade(self.usuario1, self.usuario2)
        self.assertFalse(sucesso)
        self.assertIn("pendente", erro.lower())


# ──────────────────────────────────────────────────────────────────────────────
#  EXCEÇÕES
# ──────────────────────────────────────────────────────────────────────────────


class ExcecoesTests(TestCase):
    """Testa as excecoes customizadas."""

    def test_permissao_negada_status_403(self):
        exc = PermissaoNegadaException()
        self.assertEqual(exc.status_code, 403)

    def test_permissao_negada_tem_detail(self):
        exc = PermissaoNegadaException()
        self.assertIsNotNone(exc.detail)

    def test_permissao_negada_mensagem_customizada(self):
        exc = PermissaoNegadaException("Acesso negado ao recurso.")
        self.assertIn("Acesso negado", str(exc.detail))


# ──────────────────────────────────────────────────────────────────────────────
#  PERMISSÕES
# ──────────────────────────────────────────────────────────────────────────────


class PermissaoTests(APITestCase):
    """Testa as permissoes customizadas via endpoints reais."""

    def setUp(self):
        self.verificado = Usuario.objects.create_user(
            email="verificado@exemplo.com",
            password="Teste123!@#",  # nosec
            nome_completo="Verificado",
            email_verificado=True,
            ativo=True,
        )
        self.nao_verificado = Usuario.objects.create_user(
            email="naoverificado@exemplo.com",
            password="Teste123!@#",  # nosec
            nome_completo="Nao Verificado",
            email_verificado=False,
            ativo=True,
        )

    def test_usuario_verificado_autenticado(self):
        """Usuario verificado consegue autenticar sem erro."""
        self.client.force_authenticate(user=self.verificado)
        self.assertTrue(self.verificado.email_verificado)
        self.assertTrue(self.verificado.ativo)

    def test_usuario_nao_verificado_bloqueado_em_amizade(self):
        """Usuario nao verificado e bloqueado ao tentar enviar solicitacao."""
        sucesso, erro = processar_solicitacao_amizade(
            remetente=self.nao_verificado,
            destinatario=self.verificado,
        )
        self.assertFalse(sucesso)
        self.assertIsNotNone(erro)
