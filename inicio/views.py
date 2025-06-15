from django.shortcuts import render

def inicio(request):
    return render(request, 'inicio/inicio.html')

# seu_app_django/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import uuid

@csrf_exempt # Importante para permitir POSTs de apps externos sem o token CSRF
def upload_video(request):
    if request.method == 'POST':
        # 'video_file' é o nome da "chave" que o app Android enviará
        video_file = request.FILES.get('video_file')

        if not video_file:
            return JsonResponse({'status': 'error', 'message': 'Nenhum arquivo enviado.'}, status=400)

        # Gera um nome de arquivo único para evitar colisões
        # Ex: 1234abcd-5678-efgh-9012-ijklmnopqrst.mp4
        file_extension = video_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Salva o arquivo no local de armazenamento padrão do Django
        # (que pode ser o disco local ou um serviço como o S3, dependendo da sua configuração em settings.py)
        file_path = default_storage.save(f'videos/{unique_filename}', video_file)

       # Versão corrigida e completa
        file_url = request.build_absolute_uri(default_storage.url(file_path))

        # Retorna uma resposta de sucesso para o app Android
        return JsonResponse({
            'status': 'success',
            'message': 'Upload bem-sucedido!',
            'file_url': file_url
        })

    return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)