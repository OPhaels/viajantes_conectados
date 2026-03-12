from rest_framework import serializers
from .models import Pais, PlanoViagem, EnderecoPlano, OfertaResidencia
from apps.usuarios.serializers import UsuarioPerfilSerializer
from django.utils.translation import gettext_lazy as _


class PaisSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Pais."""
    
    class Meta:
        model = Pais
        fields = ['id', 'codigo_iso', 'nome', 'nome_completo', 'continente', 
                  'latitude', 'longitude', 'imagem', 'ativo']
        read_only_fields = ['id']


class EnderecoPlanoSerializer(serializers.ModelSerializer):
    """Serializer para EnderecoPlano."""
    
    class Meta:
        model = EnderecoPlano
        fields = ['id', 'cep', 'endereco', 'numero', 'bairro', 'cidade', 
                  'estado', 'pais_texto', 'latitude', 'longitude']


class OfertaResidenciaSerializer(serializers.ModelSerializer):
    """Serializer para OfertaResidencia."""
    
    class Meta:
        model = OfertaResidencia
        fields = ['id', 'nome_anfitriao', 'contato_anfitriao', 'descricao_local']


class PlanoViagemSerializer(serializers.ModelSerializer):
    """Serializer completo para PlanoViagem."""
    
    usuario = UsuarioPerfilSerializer(read_only=True)
    pais_destino = PaisSerializer(read_only=True)
    pais_destino_id = serializers.PrimaryKeyRelatedField(
        queryset=Pais.objects.all(),
        write_only=True,
        source='pais_destino'
    )
    endereco_plano = EnderecoPlanoSerializer(read_only=True)
    oferta_residencia = OfertaResidenciaSerializer(read_only=True)
    motivo_viagem_display = serializers.CharField(
        source='get_motivo_viagem_display',
        read_only=True
    )
    nivel_privacidade_display = serializers.CharField(
        source='get_nivel_privacidade_display',
        read_only=True
    )
    duracao_dias = serializers.SerializerMethodField()
    
    class Meta:
        model = PlanoViagem
        fields = [
            'uuid', 'usuario', 'pais_destino', 'pais_destino_id',
            'cidade_destino', 'regiao_destino', 'data_inicio', 'data_fim',
            'flexibilidade_datas', 'motivo_viagem', 'motivo_viagem_display',
            'descricao', 'nivel_privacidade', 'nivel_privacidade_display',
            'orcamento_diario_min', 'orcamento_diario_max', 'ativo',
            'viagem_concluida', 'data_criacao', 'data_atualizacao',
            'endereco_plano', 'oferta_residencia', 'duracao_dias'
        ]
        read_only_fields = [
            'uuid', 'usuario', 'data_criacao', 'data_atualizacao'
        ]
    
    def get_duracao_dias(self, obj):
        """Retorna a duração da viagem em dias."""
        if obj.data_fim:
            return (obj.data_fim - obj.data_inicio).days
        return None
    
    def create(self, validated_data):
        """Cria um novo PlanoViagem e associa o usuário logado."""
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class PlanoViagemListaSerializer(serializers.ModelSerializer):
    """Serializer reduzido para listagem de PlanoViagem."""
    
    usuario = UsuarioPerfilSerializer(read_only=True)
    pais_destino = PaisSerializer(read_only=True)
    motivo_viagem_display = serializers.CharField(
        source='get_motivo_viagem_display',
        read_only=True
    )
    duracao_dias = serializers.SerializerMethodField()
    
    class Meta:
        model = PlanoViagem
        fields = [
            'uuid', 'usuario', 'pais_destino', 'cidade_destino',
            'data_inicio', 'data_fim', 'motivo_viagem', 'motivo_viagem_display',
            'nivel_privacidade', 'ativo', 'duracao_dias'
        ]
        read_only_fields = fields
    
    def get_duracao_dias(self, obj):
        """Retorna a duração da viagem em dias."""
        if obj.data_fim:
            return (obj.data_fim - obj.data_inicio).days
        return None
