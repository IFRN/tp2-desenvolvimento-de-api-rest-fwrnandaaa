from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, Voto
from .serializers import EleitorSerializer, EleicaoSerializer, CandidatoSerializer, AptidaoEleitorSerializer, VotoSerializer, VotacaoInputSerializer
from rest_framework.decorators import api_view

# Create your views here.
class EleitorViewSet(viewsets.ModelViewSet):
    queryset = Eleitor.objects.all()
    serializer_class = EleitorSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['nome', 'email', 'cpf']
    filterset_fields = ['ativo']
class EleicaoViewSet(viewsets.ModelViewSet):
    queryset = Eleicao.objects.all()
    serializer_class = EleicaoSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['titulo']
    ordering_fields = ['data_inicio']
    filterset_fields = ['tipo', 'status', 'criado_por']

    @action(detail=True, methods=['post'], url_path='votar')
    def votar(self, request, pk=None):
        data = request.data.copy()
        data['eleicao_id'] = pk
        serializer = VotacaoInputSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated = serializer.validated_data
        eleicao = validated['eleicao']
        candidato = validated.get('candidato')
        em_branco = validated.get('em_branco', False)
        token = token_urlsafe(32)
        try:
            voto = Voto.objects.create(
                eleicao=eleicao,
                candidato=candidato,
                em_branco=em_branco,
                comprovante_hash=token,
            )
        except IntegrityError:
            return Response(
                {'detail': 'Eleitor já votou nesta eleição.'},
                status=status.HTTP_409_CONFLICT,
            )
        qr_code_url = f"/eleicoes_api/comprovantes/qr/?token={token}"
        candidato_display = f"{candidato.nome_urna} (#{candidato.numero})" if candidato else 'BRANCO'
        return Response(
            {
                'mensagem': 'Voto registrado com sucesso. Guarde o seu comprovante.',
                'comprovante': {
                    'token': token,
                    'eleicao': eleicao.titulo,
                    'candidato': candidato_display,
                    'data_hora': voto.data_hora,
                    'qr_code_url': qr_code_url,
                },
            },
            status=status.HTTP_201_CREATED,
        )

class CandidatoViewSet(viewsets.ModelViewSet):
    queryset = Candidato.objects.all()
    serializer_class = CandidatoSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['nome', 'nome_urna', 'partido_ou_chapa']
    filterset_fields = ['eleicao']
class AptidaoEleitorViewSet(viewsets.ModelViewSet):
    queryset = AptidaoEleitor.objects.all()
    serializer_class = AptidaoEleitorSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['eleitor__nome', 'eleicao__titulo']
    select_related_fields = ['eleitor', 'eleicao']
class VotoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VotoSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['candidato__nome_urna', 'eleicao__titulo']
    filterset_fields = ['eleicao', 'candidato', 'em_branco']
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        vt = Voto.objects.all()
        eleicoes = self.request.query_params.get('eleicao') or self.request.query_params.get('eleicao_id')
        if eleicoes:
            try:
                eid = int(eleicoes)
                vt = vt.filter(eleicao_id=eid)
            except (TypeError, ValueError):
                vt = vt.none()
        return vt

@api_view(['GET'])
def verificar_comprovante(request):
    token = request.query_params.get('token')
    if not token:
        return Response({'valido': False, 'mensagem': 'Comprovante inválido.'}, status=status.HTTP_404_NOT_FOUND)
    try:
        voto = Voto.objects.select_related('eleicao', 'candidato').get(comprovante_hash=token)
    except Voto.DoesNotExist:
        return Response({'valido': False, 'mensagem': 'Comprovante inválido.'}, status=status.HTTP_404_NOT_FOUND)
    candidato_display = voto.candidato.nome_urna if voto.candidato else 'BRANCO'
    return Response({
        'eleicao': voto.eleicao.titulo,
        'candidato': candidato_display,
        'data_hora': voto.data_hora,
        'valido': True,
    })

@api_view(['GET'])
def comprovante_qr(request):
    token = request.query_params.get('token')
    if not token:
        return Response({'detail': 'Token obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
    verificacao_url = f"/eleicoes_api/verificar-comprovante/?token={token}"
    img = qrcode.make(verificacao_url)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')