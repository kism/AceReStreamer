"""Instances for mapping objects, separate folder to avoid circular import."""

from acerestreamer.utils.content_id_infohash_mapping import ContentIDInfohashMapping
from acerestreamer.utils.xc import ContentIDXCIdMapping

content_id_xc_id_mapping: ContentIDXCIdMapping = ContentIDXCIdMapping()
content_id_infohash_mapping: ContentIDInfohashMapping = ContentIDInfohashMapping()
