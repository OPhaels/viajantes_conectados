from rest_framework import serializers
from .models import SolicitacaoAmizade, Amizade
from apps.usuarios.serializers import UsuarioPerfilSerializer


class SolicitacaoAmizadeSerializer(serializers.ModelSerializer):
    """Serializer para SolicitacaoAmizade."""
    
    remetente = UsuarioPerfilSerializer(read_only=True)
    destinatario = UsuarioPerfilSerializer(read_only=True)
    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=None,  
        write_only=True,
        source='destinatario'
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = SolicitacaoAmizade
        fields = [
            'uuid', 'remetente', 'destinatario', 'destinatario_id',
            'mensagem', 'status', 'status_display', 'data_criacao', 'data_resposta'
        ]
        read_only_fields = ['uuid', 'data_criacao', 'data_resposta']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permitir qualquer usuário como destinatário
        if hasattr(self.fields['destinatario_id'], 'child_relation'):
            pass
        else:
            from apps.usuarios.models import Usuario
            self.fields['destinatario_id'].queryset = Usuario.objects.all()
    
    def create(self, validated_data):
        """Cria uma nova solicitação de amizade."""
        validated_data['remetente'] = self.context['request'].user
        return super().create(validated_data)


class AmizadeSerializer(serializers.ModelSerializer):
    """Serializer para Amizade."""
    
    usuario1 = UsuarioPerfilSerializer(read_only=True)
    usuario2 = UsuarioPerfilSerializer(read_only=True)
    
    class Meta:
        model = Amizade
        fields = ['uuid', 'usuario1', 'usuario2', 'data_criacao', 'ativa']
        read_only_fields = ['uuid', 'data_criacao']
