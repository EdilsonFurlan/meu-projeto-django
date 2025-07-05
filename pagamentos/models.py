from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractUser, BaseUserManager

# ----------------------------------------------------------------------
# CRIAR ESTA NOVA CLASSE: UsuarioManager
# Este é o "gerente" que sabe criar usuários usando email.
# ----------------------------------------------------------------------
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Cria e salva um usuário com o email e senha fornecidos.
        """
        if not email:
            raise ValueError('O campo de Email é obrigatório')
        email = self.normalize_email(email)
        # O username pode ser o próprio email ou outro campo que você queira
        username = extra_fields.pop('username', email) 
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

# ----------------------------------------------------------------------
# ALTERAR SUA CLASSE EXISTENTE: Usuario
# ----------------------------------------------------------------------
class Usuario(AbstractUser):
    # O email deve ser único, pois é o novo identificador de login.
    email = models.EmailField('email address', unique=True)
    
    # Diz ao Django que o campo 'email' será usado para o login.
    USERNAME_FIELD = 'email'
    
    # O 'username' padrão do Django agora é opcional.
    username = models.CharField(max_length=150, blank=True)
    
    # Diz ao Django que, ao criar um superusuário, ele não deve pedir pelo username.
    REQUIRED_FIELDS = []

    # Conecta o nosso novo gerente ao modelo.
    objects = UsuarioManager()

    # Seus campos customizados continuam aqui.
    validade_pagamento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.email

    def pagamento_esta_valido(self):
        return self.validade_pagamento and self.validade_pagamento >= timezone.now().date()

    def ativar_plano(self, dias):
        self.validade_pagamento = timezone.now().date() + timedelta(days=dias)
        self.save()

    
class Plano(models.Model):
    nome = models.CharField(max_length=100)
    dias = models.PositiveIntegerField()
    descricao = models.TextField(blank=True)

    preco_unico = models.DecimalField(max_digits=10, decimal_places=2)
    preco_recorrente = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,  # ← permite valor nulo
        blank=True  # ← opcional no admin
    )

    def __str__(self):
        return self.nome