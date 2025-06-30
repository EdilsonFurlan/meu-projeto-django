from django.urls import path
from .views import status_pagamento, ativar_plano, LoginComTokenView


urlpatterns = [
    path('status-pagamento/', status_pagamento),
    path('ativar-plano/', ativar_plano),
    path('login/', LoginComTokenView.as_view()),
]