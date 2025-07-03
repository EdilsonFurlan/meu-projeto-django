from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Usuario(AbstractUser):
    # ***** INÍCIO DA CORREÇÃO *****

    # 1. Diz ao Django que o campo 'email' será usado para o login.
    USERNAME_FIELD = 'email'

    # 2. O email deve ser único, pois é o novo identificador de login.
    email = models.EmailField(('email address'), unique=True)

    # 3. O 'username' padrão do Django agora se torna opcional.
    #    Removemos a exigência de ser único, pois não será mais usado para login.
    username = models.CharField(max_length=150, blank=True)

    # 4. Diz ao Django que, ao criar um superusuário, ele não deve pedir pelo username.
    REQUIRED_FIELDS = []

    # ***** FIM DA CORREÇÃO *****

    # Seus campos customizados continuam aqui, perfeitos como estão.
    validade_pagamento = models.DateField(null=True, blank=True)

    def pagamento_esta_valido(self):
        return self.validade_pagamento and self.validade_pagamento >= timezone.now().date()

    def ativar_plano(self, dias):
        self.validade_pagamento = timezone.now().date() + timedelta(days=dias)
        self.save()
