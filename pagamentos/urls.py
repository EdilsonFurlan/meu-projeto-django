from django.urls import path
from .views import status_pagamento, ativar_plano, LoginComTokenView, vencer_plano_teste, renovar_plano_teste, register_and_activate,listar_planos


urlpatterns = [
    path('status-pagamento/', status_pagamento),
    path('ativar-plano/', ativar_plano),
    path('login/', LoginComTokenView.as_view()),

    # NOVAS ROTAS PARA TESTE
    path('teste/vencer-plano/', vencer_plano_teste),
    path('teste/renovar-plano/', renovar_plano_teste),
    path('register-and-activate/', register_and_activate),
    path('planos/', listar_planos, name='listar_planos'),
]