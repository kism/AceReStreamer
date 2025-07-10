"""Instances for mapping objects, separate folder to avoid circular import."""

from acerestreamer.services.xc.category_id_mapping import CategoryXCCategoryIDMapping
from acerestreamer.services.xc.content_id_xc_id_mapping import ContentIDXCIdMapping
from acerestreamer.utils.content_id_infohash_mapping import ContentIDInfohashMapping

content_id_xc_id_mapping: ContentIDXCIdMapping = ContentIDXCIdMapping()
content_id_infohash_mapping: ContentIDInfohashMapping = ContentIDInfohashMapping()
category_xc_category_id_mapping: CategoryXCCategoryIDMapping = CategoryXCCategoryIDMapping()
