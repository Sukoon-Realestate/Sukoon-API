from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.chat.services.search import discover


class MessageSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            discover(request), headers={"Cache-Control": "private, no-store"}
        )


class ConversationLibraryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        return Response(
            discover(request, id), headers={"Cache-Control": "private, no-store"}
        )
