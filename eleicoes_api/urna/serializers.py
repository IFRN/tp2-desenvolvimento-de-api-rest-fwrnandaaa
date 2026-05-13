from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import FieldDoesNotExist

from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, Voto

class EleitorSerializer(serializers.ModelSerializer):
    cpf = serializers.RegexField(
        regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
        max_length=14,
        error_messages={'invalid': 'CPF deve estar no formato 000.000.000-00'}
    )

    class Meta:
        model = Eleitor
        fields = '__all__'
class EleicaoSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    total_candidatos = serializers.IntegerField(source='candidatos.count', read_only=True)
    total_aptos = serializers.IntegerField(source='registros_votacao.count', read_only=True)
    def get_status_display(self, obj):
        return obj.get_status_display()

    class Meta:
        model = Eleicao
        fields = '__all__'
class CandidatoSerializer(serializers.ModelSerializer):
    eleicao_titulo = serializers.CharField(source='eleicao.titulo', read_only=True)
    class Meta:
        model = Candidato
        fields = '__all__'

    def validate_numero(self, value):
        if value == 0:
            raise serializers.ValidationError('Número não pode ser zero.')
        return value


class AptidaoEleitorSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.CharField(source='eleitor.nome', read_only=True)
    eleicao_titulo = serializers.CharField(source='eleicao.titulo', read_only=True)
    class Meta:
        model = AptidaoEleitor
        fields = '__all__'
class VotoSerializer(serializers.ModelSerializer):
    candidato_nome_urna = serializers.CharField(source='candidato.nome_urna', read_only=True, allow_null=True)
    em_branco_display = serializers.SerializerMethodField()
    class Meta:
        model = Voto
        fields = ['id', 'eleicao', 'candidato', 'candidato_nome_urna', 'em_branco', 'em_branco_display', 'data_hora']
        read_only_fields = ['id', 'eleicao', 'candidato', 'candidato_nome_urna', 'em_branco', 'em_branco_display', 'data_hora']

    def get_em_branco_display(self, obj):
        return 'BRANCO' if obj.em_branco else None


class VotacaoInputSerializer(serializers.Serializer):
    eleitor_id = serializers.IntegerField()
    eleicao_id = serializers.IntegerField()
    candidato_id = serializers.IntegerField(required=False, allow_null=True)
    em_branco = serializers.BooleanField(default=False)

    def validate(self, data):
        eleitor_id = data.get('eleitor_id')
        eleicao_id = data.get('eleicao_id')
        candidato_id = data.get('candidato_id', None)
        em_branco = data.get('em_branco', False)
        try:
            eleitor = Eleitor.objects.get(pk=eleitor_id)
        except Eleitor.DoesNotExist:
            raise serializers.ValidationError({'eleitor_id': 'Eleitor não encontrado.'})

        try:
            eleicao = Eleicao.objects.get(pk=eleicao_id)
        except Eleicao.DoesNotExist:
            raise serializers.ValidationError({'eleicao_id': 'Eleição não encontrada.'})

        if eleicao.status != 'aberta':
            raise serializers.ValidationError({'eleicao_id': 'Eleição não está aberta.'})

        now = timezone.now()
        if not (eleicao.data_inicio <= now <= eleicao.data_fim):
            raise serializers.ValidationError({'eleicao_id': 'Eleição fora do período de votação.'})

        if not AptidaoEleitor.objects.filter(eleitor=eleitor, eleicao=eleicao).exists():
            raise serializers.ValidationError({'eleitor_id': 'Eleitor não está apto para esta eleição.'})

        try:
            Voto._meta.get_field('eleitor')
            if Voto.objects.filter(eleitor=eleitor, eleicao=eleicao).exists():
                raise serializers.ValidationError({'eleitor_id': 'Eleitor já votou nesta eleição.'})
        except Exception:
            pass

        if candidato_id is not None:
            try:
                candidato = Candidato.objects.get(pk=candidato_id)
            except Candidato.DoesNotExist:
                raise serializers.ValidationError({'candidato_id': 'Candidato não encontrado.'})
            if candidato.eleicao_id != eleicao.id:
                raise serializers.ValidationError({'candidato_id': 'Candidato não pertence a essa eleição.'})

        has_candidato = candidato_id is not None
        if has_candidato == bool(em_branco):
            raise serializers.ValidationError('Informe exatamente um: `candidato_id` ou `em_branco=True`.')

        data['eleitor'] = eleitor
        data['eleicao'] = eleicao
        data['candidato'] = candidato if candidato_id is not None else None
        return data