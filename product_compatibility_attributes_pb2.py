# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: com/here/schema/rib/v2/product_compatibility_attributes.proto
# Protobuf Python Version: 5.27.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    1,
    '',
    'com/here/schema/rib/v2/product_compatibility_attributes.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n=com/here/schema/rib/v2/product_compatibility_attributes.proto\x12\x16\x63om.here.schema.rib.v2\"\xb7\x02\n\x14VersionCompatibility\x12\x43\n\x06region\x18\x01 \x01(\x0e\x32\x33.com.here.schema.rib.v2.VersionCompatibility.Region\x12\x0b\n\x03\x64vn\x18\x02 \x01(\t\x12;\n\x08\x63\x61talogs\x18\x03 \x03(\x0b\x32).com.here.schema.rib.v2.CompatibleCatalog\"\x8f\x01\n\x06Region\x12\x11\n\rREGION_UNKOWN\x10\x00\x12\x07\n\x03\x41NT\x10\x01\x12\x08\n\x04\x41PAC\x10\x02\x12\x06\n\x02\x41U\x10\x03\x12\x07\n\x03\x45\x45U\x10\x04\x12\x07\n\x03WEU\x10\x05\x12\x07\n\x03MEA\x10\x06\x12\x06\n\x02NA\x10\x07\x12\x06\n\x02RN\x10\x08\x12\x07\n\x03SAM\x10\t\x12\x07\n\x03TWN\x10\n\x12\x07\n\x03\x43HN\x10\x0b\x12\x06\n\x02HK\x10\x0c\x12\t\n\x05MACAU\x10\r\"\x85\x01\n\x11\x43ompatibleCatalog\x12\x39\n\x0c\x63\x61talog_type\x18\x01 \x01(\x0e\x32#.com.here.schema.rib.v2.CatalogType\x12\x0b\n\x03hrn\x18\x02 \x01(\t\x12\x13\n\x0bmin_version\x18\x03 \x01(\r\x12\x13\n\x0bmax_version\x18\x04 \x01(\r*V\n\x0b\x43\x61talogType\x12\x18\n\x14\x43\x41TALOG_TYPE_UNKNOWN\x10\x00\x12\x14\n\x10HERE_MAP_CONTENT\x10\x01\x12\x17\n\x13\x45XTERNAL_REFERENCES\x10\x02\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'com.here.schema.rib.v2.product_compatibility_attributes_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CATALOGTYPE']._serialized_start=539
  _globals['_CATALOGTYPE']._serialized_end=625
  _globals['_VERSIONCOMPATIBILITY']._serialized_start=90
  _globals['_VERSIONCOMPATIBILITY']._serialized_end=401
  _globals['_VERSIONCOMPATIBILITY_REGION']._serialized_start=258
  _globals['_VERSIONCOMPATIBILITY_REGION']._serialized_end=401
  _globals['_COMPATIBLECATALOG']._serialized_start=404
  _globals['_COMPATIBLECATALOG']._serialized_end=537
# @@protoc_insertion_point(module_scope)
