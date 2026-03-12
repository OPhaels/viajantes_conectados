from rest_framework import serializers
from .models import Usuario
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _


class UsuarioRegistroSerializer(serializers.ModelSerializer):
    """Serializer para registro de novo usuário."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = Usuario
        fields = [
            'email', 'nome_completo', 'data_nascimento', 'telefone',
            'pais_residencia', 'cidade_residencia', 'password', 'password2'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'nome_completo': {'required': True},
        }
    
    def validate(self, attrs):
        """Valida se as senhas correspondem."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {'password': _('As senhas não correspondem.')}
            )
        return attrs
    
    def create(self, validated_data):
        """Cria um novo usuário."""
        validated_data.pop('password2')
        usuario = Usuario.objects.create_user(**validated_data)
        return usuario


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    """Serializer para perfil público de usuário."""
    
    class Meta:
        model = Usuario
        fields = [
            'uuid', 'nome_completo', 'foto_perfil', 'data_nascimento',
            'pais_residencia', 'cidade_residencia', 'biografia',
            'data_criacao'
        ]
        read_only_fields = fields


class UsuarioDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para o usuário autenticado."""
    
    class Meta:
        model = Usuario
        fields = [
            'uuid', 'email', 'nome_completo', 'data_nascimento', 'telefone',
            'pais_residencia', 'cidade_residencia', 'biografia', 'foto_perfil',
            'perfil_publico', 'mostrar_email', 'mostrar_telefone',
            'email_verificado', 'ativo', 'data_criacao', 'ultimo_acesso'
        ]
        read_only_fields = [
            'uuid', 'email', 'email_verificado', 'ativo',
            'data_criacao', 'ultimo_acesso'
        ]


class UsuarioEditarSerializer(serializers.ModelSerializer):
    """Serializer para edição do perfil do usuário."""
    
    password_atual = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )
    nova_senha = serializers.CharField(
        write_only=True,
        required=False,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirmar_senha = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = Usuario
        fields = [
            'nome_completo', 'data_nascimento', 'telefone',
            'pais_residencia', 'cidade_residencia', 'biografia',
            'foto_perfil', 'perfil_publico', 'mostrar_email',
            'mostrar_telefone', 'password_atual', 'nova_senha',
            'confirmar_senha'
        ]
    
    def validate(self, attrs):
        """Valida alterações de senha."""
        nova_senha = attrs.get('nova_senha')
        confirmar_senha = attrs.get('confirmar_senha')
        
        if nova_senha or confirmar_senha:
            # Se uma foi fornecida, ambas são obrigatórias
            if not nova_senha or not confirmar_senha:
                raise serializers.ValidationError(
                    _('Ambos os campos de senha devem ser preenchidos.')
                )
            
            if nova_senha != confirmar_senha:
                raise serializers.ValidationError(
                    {'nova_senha': _('As senhas não correspondem.')}
                )
            
            # Verificar senha atual
            password_atual = attrs.get('password_atual')
            if not password_atual:
                raise serializers.ValidationError(
                    {'password_atual': _('A senha atual é obrigatória para mudar a senha.')}
                )
            
            usuario = self.context['request'].user
            if not usuario.check_password(password_atual):
                raise serializers.ValidationError(
                    {'password_atual': _('Senha atual incorreta.')}
                )
        
        return attrs
    
    def update(self, instance, validated_data):
        """Atualiza o perfil do usuário."""
        # Remover campos de senha
        nova_senha = validated_data.pop('nova_senha', None)
        validated_data.pop('password_atual', None)
        validated_data.pop('confirmar_senha', None)
        
        # Atualizar outros campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Atualizar senha se fornecida
        if nova_senha:
            instance.set_password(nova_senha)
        
        instance.save()
        return instance


class UsuarioListaSerializer(serializers.ModelSerializer):
    """Serializer para listar usuários (sem sensíveis)."""
    
    class Meta:
        model = Usuario
        fields = [
            'uuid', 'nome_completo', 'foto_perfil', 'pais_residencia',
            'cidade_residencia', 'biografia', 'data_criacao'
        ]
        read_only_fields = fields
