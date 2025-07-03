# Imports existentes e novos que são necessários
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model, authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token


# --------------------------------------------------------------------------
# PARTE 1: CRIAR ESTA NOVA CLASSE (AuthTokenSerializer)
# Esta classe não existe no seu arquivo. Ela é nova e necessária.
# Sua função é dizer ao Django para aceitar 'email' e 'password' no login.
# --------------------------------------------------------------------------
class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, label="Email")
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
        label="Password"
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Como você definiu USERNAME_FIELD = 'email' no seu modelo Usuario,
            # o sistema de autenticação do Django agora entende que o 'username'
            # que ele espera é, na verdade, o campo de email.
            user = authenticate(request=self.context.get('request'), username=email, password=password)

            if not user:
                msg = 'Não foi possível fazer o login com as credenciais fornecidas.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'É necessário fornecer "email" e "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


# --------------------------------------------------------------------------
# PARTE 2: ALTERAR A SUA CLASSE EXISTENTE (LoginComTokenView)
# Vamos substituir a sua implementação antiga pela nova, que usa o serializer.
# --------------------------------------------------------------------------
class LoginComTokenView(ObtainAuthToken):
    # Esta linha diz à view para usar a nossa nova classe de serializer.
    serializer_class = EmailAuthTokenSerializer

    # Este método post agora usa a lógica padrão do DRF com nosso serializer customizado.
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            # user.get_username() vai retornar o email, pois definimos isso no modelo
            'username': user.get_username(),
            'validade': user.validade_pagamento,
            'pagamento_ativo': user.pagamento_esta_valido(),
        })


# --------------------------------------------------------------------------
# PARTE 3: MANTER O RESTO DO SEU CÓDIGO (SEM ALTERAÇÕES)
# Todas as suas outras views continuam exatamente como estavam.
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def status_pagamento(request):
    usuario = request.user
    return Response({
        "pagamento_ativo": usuario.pagamento_esta_valido(),
        "validade": usuario.validade_pagamento
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vencer_plano_teste(request):
    usuario = request.user
    usuario.validade_pagamento = timezone.now().date() - timedelta(days=1)
    usuario.save()
    return Response({
        'msg': 'Plano do usuário forçado para o estado de vencido.',
        'nova_validade': usuario.validade_pagamento,
        'pagamento_ativo': usuario.pagamento_esta_valido()
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def renovar_plano_teste(request):
    usuario = request.user
    hoje = timezone.now().date()
    data_base = usuario.validade_pagamento if usuario.pagamento_esta_valido() else hoje
    try:
        dias_para_adicionar = int(request.data.get('dias', 30))
    except (ValueError, TypeError):
        dias_para_adicionar = 30
    usuario.validade_pagamento = data_base + timedelta(days=dias_para_adicionar)
    usuario.save()
    return Response({
        'msg': f'Plano renovado por {dias_para_adicionar} dias.',
        'nova_validade': usuario.validade_pagamento,
        'pagamento_ativo': usuario.pagamento_esta_valido()
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
        user = User.objects.create_user(username=username, email=email, password=password)
        user.ativar_plano(dias=int(plan_days))
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'status': 'success',
            'message': 'Conta criada e plano ativado com sucesso!',
            'token': token.key,
            'username': user.username,
            'pagamento_ativo': user.pagamento_esta_valido(),
            'validade': user.validade_pagamento
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)