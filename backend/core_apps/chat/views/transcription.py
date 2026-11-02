from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from core_apps.features.renderers import FeatureJsonRenderer
from ..models import Conversation, VoiceTranscription
from .group_attachments import accessible_attachment
from ..services.transcription import request_transcription, payload, available


class VoiceTranscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    renderer_classes = [FeatureJsonRenderer]

    def attachment(self, request, id, attachment_id):
        item = accessible_attachment(
            get_object_or_404(Conversation, id=id), request.user, identity=attachment_id
        )
        if item.kind != "voice" or not item.message_id:
            raise NotFound()
        return item

    def get(self, request, id, attachment_id):
        item = self.attachment(request, id, attachment_id)
        job = VoiceTranscription.objects.filter(
            attachment=item, fingerprint=item.fingerprint
        ).first()
        response = Response(
            payload(job)
            if job
            else {
                "state": "idle" if available() else "unavailable",
                "text": "",
                "error_code": "",
            }
        )
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request, id, attachment_id):
        response = Response(
            request_transcription(
                self.attachment(request, id, attachment_id), request.user
            )
        )
        response["Cache-Control"] = "no-store"
        return response
