
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Usuario(AbstractUser):
    validade_pagamento = models.DateField(null=True, blank=True)

    def pagamento_esta_valido(self):
        return self.validade_pagamento and self.validade_pagamento >= timezone.now().date()

    def ativar_plano(self, dias):
        self.validade_pagamento = timezone.now().date() + timedelta(days=dias)
        self.save()
