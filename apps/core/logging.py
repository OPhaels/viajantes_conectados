"""
Configurações de logging seguras para a aplicação.
"""

import logging
import re
from django.conf import settings


class HideSensitiveDataFilter(logging.Filter):
    """
    Filtro de logging que remove ou mascara dados sensíveis dos logs.
    
    Remove/mascara:
    - Senhas (password, senha, etc.)
    - Tokens de autenticação
    - Chaves API
    - Dados pessoais sensíveis
    """
    
    def __init__(self):
        super().__init__()
        
        # Padrões para identificar dados sensíveis
        self.sensitive_patterns = [
            # Senhas
            (r'("password"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("password2"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("senha"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("old_password"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            
            # Tokens
            (r'("token"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("access"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("refresh"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'(Bearer\s+)[^\s]+', r'\1[FILTERED]'),
            
            # Chaves API e secrets
            (r'("SECRET_KEY"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("API_KEY"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("DATABASE_URL"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            
            # Dados pessoais
            (r'("telefone"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("cpf"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
            (r'("rg"\s*:\s*)"[^"]*"', r'\1"[FILTERED]"'),
        ]
    
    def filter(self, record):
        """Filtra a mensagem do log removendo dados sensíveis."""
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
        else:
            message = str(record.msg)
        
        # Aplicar filtros de dados sensíveis
        for pattern, replacement in self.sensitive_patterns:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        # Atualizar a mensagem do record
        record.msg = message
        record.message = message
        
        return True