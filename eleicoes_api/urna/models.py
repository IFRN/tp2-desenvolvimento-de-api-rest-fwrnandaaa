from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
class Eleitor(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
class Eleicao(models.Model):
    tipo_eleicao = [
        ('estudantil', 'Eleição Estudantil'),
        ('sindical', 'Eleição Sindical'),
        ('associacao', 'Eleição de Associação'),
        ('condominio', 'Eleição de Condômino'),
        ('conselho', 'Eleição de Conselho'),
        ('outra', 'Outra Eleição'),
    ]

    status_eleicao = [
        ('rascunho', 'Rascunho'),
        ('aberta', 'Aberta'),
        ('encerrada', 'Encerrada'),
        ('apurada', 'Apurada'),
    ]
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo= models.CharField(max_length=20, choices=tipo_eleicao)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    status = models.CharField(max_length=20, choices=status_eleicao, default='rascunho')
    permite_branco = models.BooleanField(default=True)
    criado_por = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='eleicoes_criadas')

    def __str__(self):
        return self.titulo
class Candidato(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='candidatos')
    numero = models.PositiveIntegerField()
    nome = models.CharField(max_length=100)
    nome_urna = models.CharField(max_length=50)
    partido_ou_chapa = models.CharField(max_length=100, blank=True)
    proposta  = models.TextField(blank=True)
    foto_url = models.URLField(blank=True)

    def __str__(self):
        return self.nome
class AptidaoEleitor(models.Model):
    eleitor = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='registros_votacao')
    eleicao = models.ForeignKey(Eleicao, on_delete=models.PROTECT, related_name='registros_votacao')
    data_hora = models.DateTimeField(auto_now_add=True)
class Voto(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.PROTECT, related_name='votos')
    candidato = models.ForeignKey(Candidato, on_delete=models.PROTECT, related_name='votos', null=True, blank=True)
    em_branco = models.BooleanField(default=False)
    data_hora = models.DateTimeField(auto_now_add=True)
    comprovante_hash = models.CharField(max_length=64, unique=True)

    def clean(self):
        super().clean()
        if self.em_branco and self.candidato is not None:
            raise ValidationError({'candidato': "Se 'em_branco' for True, 'candidato' deve ser None."})
        if (not self.em_branco) and (self.candidato is None):
            raise ValidationError({'candidato': "Se 'em_branco' for False, 'candidato' não pode ser None."})