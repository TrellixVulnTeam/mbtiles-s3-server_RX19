# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: glyphs.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x0cglyphs.proto\"n\n\x05glyph\x12\n\n\x02id\x18\x01 '
    b'\x02(\r\x12\x0e\n\x06\x62itmap\x18\x02 \x01(\x0c\x12\r\n'
    b'\x05width\x18\x03 \x02(\r\x12\x0e\n\x06height\x18\x04 '
    b'\x02(\r\x12\x0c\n\x04left\x18\x05 \x02(\x11\x12\x0b\n\x03'
    b'top\x18\x06 \x02(\x11\x12\x0f\n\x07\x61\x64vance\x18\x07 '
    b'\x02(\r\"@\n\tfontstack\x12\x0c\n\x04name\x18\x01 \x02(\t'
    b'\x12\r\n\x05range\x18\x02 \x02(\t\x12\x16\n\x06glyphs\x18'
    b'\x03 \x03(\x0b\x32\x06.glyph\"+\n\x06glyphs\x12\x1a\n\x06'
    b'stacks\x18\x01 \x03(\x0b\x32\n.fontstack*\x05\x08\x10\x10'
    b'\x80@B\x02H\x03')


_GLYPH = DESCRIPTOR.message_types_by_name['glyph']
_FONTSTACK = DESCRIPTOR.message_types_by_name['fontstack']
_GLYPHS = DESCRIPTOR.message_types_by_name['glyphs']
glyph = _reflection.GeneratedProtocolMessageType('glyph', (_message.Message,), {
    'DESCRIPTOR': _GLYPH,
    '__module__': 'glyphs_pb2'
    # @@protoc_insertion_point(class_scope:glyph)
})
_sym_db.RegisterMessage(glyph)

fontstack = _reflection.GeneratedProtocolMessageType('fontstack', (_message.Message,), {
    'DESCRIPTOR': _FONTSTACK,
    '__module__': 'glyphs_pb2'
    # @@protoc_insertion_point(class_scope:fontstack)
})
_sym_db.RegisterMessage(fontstack)

glyphs = _reflection.GeneratedProtocolMessageType('glyphs', (_message.Message,), {
    'DESCRIPTOR': _GLYPHS,
    '__module__': 'glyphs_pb2'
    # @@protoc_insertion_point(class_scope:glyphs)
})
_sym_db.RegisterMessage(glyphs)

if _descriptor._USE_C_DESCRIPTORS is False:

    DESCRIPTOR._options = None
    DESCRIPTOR._serialized_options = b'H\003'
    _GLYPH._serialized_start = 16
    _GLYPH._serialized_end = 126
    _FONTSTACK._serialized_start = 128
    _FONTSTACK._serialized_end = 192
    _GLYPHS._serialized_start = 194
    _GLYPHS._serialized_end = 237
# @@protoc_insertion_point(module_scope)