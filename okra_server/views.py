import base64
import io

import qrcode
from django.http.request import HttpRequest
from django.shortcuts import render

from okra_server import models


def registration_details(request: HttpRequest, participant_id: str):
    participant = models.Participant.objects.get(id=participant_id)
    base_url = request.build_absolute_uri("/api")

    data = f"{base_url}\n" f"{participant.id}\n" f"{participant.registration_key}"
    image = qrcode.make(data)
    image_bytes = io.BytesIO()
    image.save(image_bytes, "PNG")
    image_base64 = base64.b64encode(image_bytes.getvalue())

    return render(
        request,
        "okra_server/registration_details.html",
        {
            "base_url": base_url,
            "participant_id": participant.id,
            "registration_key": participant.registration_key,
            "qr_data": image_base64.decode("ascii"),
        },
    )
