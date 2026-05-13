from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, Voto
from .serializers import EleitorSerializer, EleicaoSerializer, CandidatoSerializer, AptidaoEleitorSerializer, VotoSerializer, VotacaoInputSerializer


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

