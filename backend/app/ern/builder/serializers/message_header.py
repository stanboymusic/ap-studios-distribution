from datetime import datetime, timezone
import uuid as _uuid

from app.ern.builder.xml_utils import sub

def build_message_header(parent, ctx, ns):
    mh = sub(parent, "MessageHeader", ns=ns)

    # Generar MessageId único por cada ERN generado
    message_id = f"AP-{_uuid.uuid4().hex[:16].upper()}"
    try:
        ctx.message_id = message_id
    except Exception:
        pass
    sub(mh, "MessageId", message_id, ns=ns)
    # Generar timestamp real en el momento de construir el ERN
    message_created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sub(mh, "MessageCreatedDateTime", message_created, ns=ns)

    sender = sub(mh, "MessageSender", ns=ns)
    sub(sender, "PartyId", ctx.sender.party_id, ns=ns)
    sub(sender, "PartyName", ctx.sender.name or "AP Studios", ns=ns)

    recipient = sub(mh, "MessageRecipient", ns=ns)
    sub(recipient, "PartyId", ctx.recipient.party_id, ns=ns)
    sub(recipient, "PartyName", ctx.recipient.name, ns=ns)
