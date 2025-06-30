from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

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