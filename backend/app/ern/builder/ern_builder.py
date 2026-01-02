from lxml import etree
from app.ern.builder.xml_utils import NSMAP, E
from app.ern.builder.serializers import (
    message_header, parties, resources, releases, deals
)
from app.ern.registry.reference_registry import ReferenceRegistry


class ErnBuilder:

    def build(self, graph):
        registry = ReferenceRegistry()

        root = etree.Element(
            E("NewReleaseMessage"),
            nsmap=NSMAP,
            AvsVersionId="4.3",
            LanguageAndScriptCode=graph["context"].language
        )

        message_header.build_message_header(root, graph["context"])
        parties.build_party_list(root, graph["parties"], registry)
        resources.build_resource_list(root, graph["resources"], registry)
        releases.build_release_list(root, graph["releases"], registry)
        deals.build_deal_list(root, graph["deals"], registry)

        return etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        )