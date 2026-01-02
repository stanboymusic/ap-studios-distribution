from lxml import etree
from datetime import datetime
import uuid

def build_message_header(root):
    header = etree.SubElement(root, "MessageHeader")

    etree.SubElement(header, "MessageThreadId").text = str(uuid.uuid4())
    etree.SubElement(header, "MessageId").text = str(uuid.uuid4())
    etree.SubElement(header, "MessageCreatedDateTime").text = datetime.utcnow().isoformat() + "Z"

    sender = etree.SubElement(header, "MessageSender")
    etree.SubElement(sender, "PartyId").text = "PA-DPIDA-202402050E-4"
    sender_party_name = etree.SubElement(sender, "PartyName")
    etree.SubElement(sender_party_name, "FullName").text = "AP Studios"

    recipient = etree.SubElement(header, "MessageRecipient")
    etree.SubElement(recipient, "PartyId").text = "PADPIDA0000000001"
    recipient_party_name = etree.SubElement(recipient, "PartyName")
    etree.SubElement(recipient_party_name, "FullName").text = "DDEX Test Recipient"

    return header