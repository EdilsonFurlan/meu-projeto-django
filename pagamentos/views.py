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

from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt


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

User = get_user_model()

@csrf_exempt
@api_view(['POST'])
def register_and_activate(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    plan_days = request.data.get('planDays')

    if not all([username, email, password, plan_days]):
        return Response({'error': 'Todos os campos são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Nome de usuário já existe.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email já cadastrado.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. Cria o usuário
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # 2. Ativa o plano para o novo usuário
        user.ativar_plano(dias=int(plan_days))
        
        # 3. (Opcional, mas recomendado) Gera um token de login para ele automaticamente
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'status': 'success',
            'message': 'Conta criada e plano ativado com sucesso!',
            'token': token.key, # Retorna o token para o app já fazer o login
            'username': user.username,
            'pagamento_ativo': user.pagamento_esta_valido(),
            'validade': user.validade_pagamento
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)