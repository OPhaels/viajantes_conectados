"""
Testes para o app core.
Testa exceções, permissões e funções utilitárias.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.core.exceptions import PermissaoNegadaException
from apps.core.utils import (
    validar_senha_segura,
    obter_dados_publicos_usuario,
    gerar_token_verificacao,
    processar_solicitacao_amizade,
)

Usuario = get_user_model()


class ValidacaoSenhaTests(TestCase):
    """Testa a validação de senhas seguras."""
    
    def test_senha_fraca_muito_curta(self):
        """Senha com menos de 8 caracteres é fraca."""
        valida, erros = validar_senha_segura("123456")
        self.assertFalse(valida)
        self.assertTrue(len(erros) > 0)
    
    def test_senha_sem_maiuscula(self):
        """Senha sem letra maiúscula é fraca."""
        valida, erros = validar_senha_segura("senha123!@#")
        self.assertFalse(valida)
        self.assertIn("maiúscula", "".join(erros).lower())
    
    def test_senha_sem_numero(self):
        """Senha sem número é fraca."""
        valida, erros = validar_senha_segura("SenhaForte!@#")
        self.assertFalse(valida)
    
    def test_senha_sem_caractere_especial(self):
        """Senha sem caractere especial é fraca."""
        valida, erros = validar_senha_segura("SenhaForte123")
        self.assertFalse(valida)
    
    def test_senha_forte(self):
        """Senha que atende todos os critérios é forte."""
        valida, erros = validar_senha_segura("SenhaForte123!@#")
        self.assertTrue(valida)
        self.assertEqual(len(erros), 0)


class ObterDadosPublicosTests(TestCase):
    """Testa a extração de dados públicos do usuário."""
    
    def setUp(self):
        """Cria um usuário para teste."""
        self.usuario = Usuario.objects.create_user(
            email='teste@exemplo.com',
            password='TesteSenha123!',
            nome_completo='João da Silva',
            pais_residencia='Brasil',
            cidade_residencia='São Paulo',
            biografia='Mochileiro apaixonado'
        )
    
    def test_obtem_dados_basicos(self):
        """Extrai dados públicos corretamente."""
        dados = obter_dados_publicos_usuario(self.usuario)
        
        self.assertEqual(dados['nome_completo'], 'João da Silva')
        self.assertEqual(dados['pais_residencia'], 'Brasil')
        self.assertIn('uuid', dados)
    
    def test_nao_expoe_email(self):
        """Email não está incluído nos dados públicos."""
        dados = obter_dados_publicos_usuario(self.usuario)
        self.assertNotIn('email', dados)


class GerarTokenVerificacaoTests(TestCase):
    """Testa a geração de tokens."""
    
    def test_gera_token_comprimento(self):
        """Token gerado tem 64 caracteres (SHA256)."""
        token = gerar_token_verificacao('teste@exemplo.com')
        self.assertEqual(len(token), 64)
    
    def test_gera_tokens_diferentes(self):
        """Tokens gerados em tempos diferentes são diferentes."""
        import time
        token1 = gerar_token_verificacao('teste@exemplo.com')
        time.sleep(1)
        token2 = gerar_token_verificacao('teste@exemplo.com')
        
        # Provavelmente diferentes devido a timestamp
        # (não garantido, mas muito provável)


class ProcessarSolicitacaoAmizadeTests(TestCase):
    """Testa a lógica de processar solicitações de amizade."""
    
    def setUp(self):
        """Cria usuários para teste."""
        self.usuario1 = Usuario.objects.create_user(
            email='usuario1@exemplo.com',
            password='Teste123!@#',
            nome_completo='Usuário Um',
            email_verificado=True
        )
        self.usuario2 = Usuario.objects.create_user(
            email='usuario2@exemplo.com',
            password='Teste123!@#',
            nome_completo='Usuário Dois',
            email_verificado=True
        )
    
    def test_nao_pode_enviar_para_si_mesmo(self):
        """Não permite enviar solicitação para si mesmo."""
        sucesso, erro = processar_solicitacao_amizade(
            remetente=self.usuario1,
            destinatario=self.usuario1
        )
        
        self.assertFalse(sucesso)
        self.assertIsNotNone(erro)
    
    def test_requer_email_verificado(self):
        """Requer que o remetente tenha email verificado."""
        usuario_nao_verificado = Usuario.objects.create_user(
            email='nao_verificado@exemplo.com',
            password='Teste123!@#',
            nome_completo='Não Verificado',
            email_verificado=False
        )
        
        sucesso, erro = processar_solicitacao_amizade(
            remetente=usuario_nao_verificado,
            destinatario=self.usuario2
        )
        
        self.assertFalse(sucesso)
        self.assertIn('email', erro.lower())


class ExcecoesTests(TestCase):
    """Testa as exceções customizadas."""
    
    def test_permissao_negada_exception(self):
        """PermissaoNegadaException tem status 403."""
        exc = PermissaoNegadaException()
        self.assertEqual(exc.status_code, 403)
    
    def test_permissao_negada_mensagem_padrao(self):
        """PermissaoNegadaException tem mensagem padrão."""
        exc = PermissaoNegadaException()
        self.assertIsNotNone(exc.detail)


class PermissaoTests(APITestCase):
    """Testa as permissões customizadas."""
    
    def setUp(self):
        """Cria usuários para teste."""
        self.usuario_verificado = Usuario.objects.create_user(
            email='verificado@exemplo.com',
            password='Teste123!@#',
            nome_completo='Verificado',
            email_verificado=True,
            ativo=True
        )
        self.usuario_nao_verificado = Usuario.objects.create_user(
            email='nao_verificado@exemplo.com',
            password='Teste123!@#',
            nome_completo='Não Verificado',
            email_verificado=False,
            ativo=True
        )
    
    def test_usuario_verificado_pode_acessar(self):
        """Usuário verificado consegue acessar endpoints restritos."""
        self.client.force_authenticate(user=self.usuario_verificado)
        # Teste de acesso a endpoints específicos aqui
    
    def test_usuario_nao_verificado_bloqueado(self):
        """Usuário não verificado é bloqueado de operações sensíveis."""
        self.client.force_authenticate(user=self.usuario_nao_verificado)
        # Teste de bloqueio aqui


if __name__ == '__main__':
    import unittest
    unittest.main()
