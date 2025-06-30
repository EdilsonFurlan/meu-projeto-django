from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def status_pagamento(request):
    usuario = request.user
    return Response({
        "pagamento_ativo": usuario.pagamento_esta_valido(),
        "validade": usuario.validade_pagamento
    })


class LoginComTokenView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({
            'token': token.key,
            'username': token.user.username,
            'validade': token.user.validade_pagamento,
            'pagamento_ativo': token.user.pagamento_esta_valido(),
        })
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ativar_plano(request):
    try:
        dias = int(request.data.get('dias', 7))
        usuario = request.user
        usuario.ativar_plano(dias)
        return Response({
            'msg': f'Plano ativado por {dias} dias',
            'validade': usuario.validade_pagamento,
            'pagamento_ativo': usuario.pagamento_esta_valido()
        })
    except:
        return Response({'erro': 'Requisição inválida'}, status=status.HTTP_400_BAD_REQUEST)
    

# pagamentos/views.py



# ... (suas views existentes: status_pagamento, LoginComTokenView, ativar_plano) ...

# NOVO ENDPOINT PARA FORÇAR O VENCIMENTO DO PLANO
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vencer_plano_teste(request):
    """
    Endpoint de teste para definir a validade do plano do usuário para ontem.
    Isso simula um plano expirado.
    """
    usuario = request.user
    # Define a data de validade para 1 dia atrás
    usuario.validade_pagamento = timezone.now().date() - timedelta(days=1)
    usuario.save()

    return Response({
        'msg': 'Plano do usuário forçado para o estado de vencido.',
        'nova_validade': usuario.validade_pagamento,
        'pagamento_ativo': usuario.pagamento_esta_valido() # Deve ser False
    })


# NOVO ENDPOINT PARA SIMULAR UMA RENOVAÇÃO
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def renovar_plano_teste(request):
    """
    Endpoint de teste que simula um pagamento bem-sucedido.
    Adiciona 30 dias à validade do plano do usuário.
    Se o plano já venceu, adiciona 30 dias a partir de hoje.
    """
    usuario = request.user
    hoje = timezone.now().date()
    
    # Se o plano já venceu, a nova validade começa a contar de hoje.
    # Se ainda está válido, adiciona 30 dias à data de validade existente.
    data_base = usuario.validade_pagamento if usuario.pagamento_esta_valido() else hoje

    try:
        # Pega a quantidade de dias do corpo da requisição, com 30 como padrão
        dias_para_adicionar = int(request.data.get('dias', 30))
    except (ValueError, TypeError):
        dias_para_adicionar = 30
    
    usuario.validade_pagamento = data_base + timedelta(days=dias_para_adicionar)
    usuario.save()
    
    return Response({
        'msg': f'Plano renovado por {dias_para_adicionar} dias.',
        'nova_validade': usuario.validade_pagamento,
        'pagamento_ativo': usuario.pagamento_esta_valido() # Deve ser True
    })