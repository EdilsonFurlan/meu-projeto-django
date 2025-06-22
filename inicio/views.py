from django.shortcuts import render

def inicio(request):
    return render(request, 'inicio/inicio.html')

# seu_app_django/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os

@csrf_exempt
def upload_video(request):
    if request.method == 'POST':
        # 1. Pega os dados do arquivo e do evento
        video_file = request.FILES.get('video_file')
        event_name = request.POST.get('event_name')
        
        # --- REMOVIDO ---
        # Não precisamos mais pegar o nome do arquivo do formulário
        # original_filename = request.POST.get('original_filename')

        # 2. Validação simplificada
        if not video_file:
            return JsonResponse({'status': 'error', 'message': 'Nenhum arquivo de vídeo enviado.'}, status=400)
        if not event_name:
            return JsonResponse({'status': 'error', 'message': 'Nome do evento não fornecido.'}, status=400)
        
        # --- REMOVIDO ---
        # A validação do nome do arquivo original não é mais necessária
        # if not original_filename:
        #     return JsonResponse({'status': 'error', 'message': 'Nome do arquivo original não fornecido.'}, status=400)

        # 3. Pega o nome do arquivo diretamente do objeto de upload
        #    O objeto 'video_file' tem um atributo '.name'
        # --- ALTERADO ---
        filename = video_file.name

        # 4. Constrói o caminho de salvamento com a pasta do evento e o nome original
        # Ex: 'eventos/Casamento Joao e Maria/video_final_12345.mp4'
        # --- ALTERADO ---
        file_path = default_storage.save(os.path.join('eventos', event_name, filename), video_file)

        # 5. Constrói a URL final para retornar ao app
        file_url = request.build_absolute_uri(default_storage.url(file_path))

        return JsonResponse({
            'status': 'success',
            'message': 'Upload bem-sucedido!',
            'file_url': file_url
        })

    return JsonResponse({'status': 'error', 'message': 'Método não permitido.'}, status=405)