from app.ern.builder.xml_utils import sub

def build_message_header(parent, ctx, ns):
    mh = sub(parent, "MessageHeader", ns=ns)

    sub(mh, "MessageId", ctx.message_id, ns=ns)
    sub(mh, "MessageCreatedDateTime", "2026-01-02T22:52:46Z", ns=ns)  # Use current time

    sender = sub(mh, "MessageSender", ns=ns)
    sub(sender, "PartyId", ctx.sender.party_id, ns=ns)
    sub(sender, "PartyName", ctx.sender.name, ns=ns)

    recipient = sub(mh, "MessageRecipient", ns=ns)
    sub(recipient, "PartyId", ctx.recipient.party_id, ns=ns)
    sub(recipient, "PartyName", ctx.recipient.name, ns=ns)