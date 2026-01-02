from app.ern.builder.xml_utils import sub

def build_message_header(parent, ctx):
    mh = sub(parent, "MessageHeader")

    sub(mh, "MessageThreadId", ctx.message.thread_id)
    sub(mh, "MessageId", ctx.message.message_id)
    sub(mh, "MessageCreatedDateTime", ctx.message.created_at.isoformat())

    sender = sub(mh, "MessageSender")
    sub(sender, "PartyId", ctx.sender.party_id)
    sub(sender, "PartyName", ctx.sender.name)

    recipient = sub(mh, "MessageRecipient")
    sub(recipient, "PartyId", ctx.recipient.party_id)
    sub(recipient, "PartyName", ctx.recipient.name)

    sub(mh, "MessageControlType", ctx.message.update_indicator)