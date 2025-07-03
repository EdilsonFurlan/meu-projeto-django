from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework import serializers # <<< IMPORTANTE: ADICIONE ESTE IMPORT
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model, authenticate # <<< IMPORTANTE: ADICIONE ESTE IMPORT
from django.views.decorators.csrf import csrf_exempt

# --- Serializer Customizado para Login com Email ---
# Este serializer diz ao Django para esperar um campo 'email' em vez de 'username'
class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email")
    password = serializers.CharField(
        label="Password",
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Tenta autenticar usando o email como username
            user = authenticate(request=self.context.get('request'),
                                username=email, password=password)

            if not user:
                # Se a autenticação falhar, tenta encontrar o usuário pelo email
                # e então autentica com o username dele. Isso cobre todas as bases.
                User = get_user_model()
                try:
                    user_obj = User.objects.get(email=email)
                    user = authenticate(request=self.context.get('request'),
                                        username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if not user:
                msg = 'Não foi possível fazer o login com as credenciais fornecidas.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'É necessário fornecer "email" e "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

# --- Views ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def status_pagamento(request):
    usuario = request.user
    return Response({
        "pagamento_ativo": usuario.pagamento_esta_valido(),
        "validade": usuario.validade_pagamento
    })

# ***** AQUI ESTÁ A CORREÇÃO PRINCIPAL *****
class LoginComTokenView(ObtainAuthToken):
    # Sobrescreve o serializer padrão para usar o nosso serializer de email
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'username': user.username,
            'validade': user.validade_pagamento,
            'pagamento_ativo': user.pagamento_esta_valido(),
        })

# O resto das suas views continua exatamente igual...

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