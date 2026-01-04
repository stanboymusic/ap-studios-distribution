from lxml import etree
from app.ern.builder.xml_utils import E
from app.ern.builder.serializers import (
    message_header, parties, resources, releases, deals
)
from app.ern.registry.reference_registry import ReferenceRegistry
from app.config.ddex import ERN_CONFIG


class ErnBuilder:

    def build(self, graph):
        if not graph["resources"]:
            raise ValueError("ResourceList cannot be empty. Add at least one track or artwork.")
        
        registry = ReferenceRegistry()
        context = graph["context"]
        config = ERN_CONFIG[(context.version, context.profile)]
        nsmap = {
            None: config["namespace"],
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }

        root = etree.Element(
            f"{{{config['namespace']}}}NewReleaseMessage",
            nsmap=nsmap,
            AvsVersionId=context.version,
            LanguageAndScriptCode="en"
        )

        message_header.build_message_header(root, context, config["namespace"])
        parties.build_party_list(root, graph["parties"], registry, config["namespace"])
        resources.build_resource_list(root, graph["resources"], registry, config["namespace"])
        releases.build_release_list(root, graph["releases"], registry, config["namespace"])
        deals.build_deal_list(root, graph["deals"], registry, config["namespace"])

        return etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        )