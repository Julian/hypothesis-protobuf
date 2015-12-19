from ctypes import c_float

from google.protobuf import reflection
from google.protobuf.descriptor import Descriptor, FieldDescriptor
from hypothesis import example, given, strategies


def type_with_value(value_strategy, *type_strategies):
    just = strategies.sampled_from(type_strategies)
    return just.flatmap(
        lambda field_type : strategies.tuples(
            strategies.just(field_type),
            value_strategy,
        )
    )


full_name = strategies.binary()
index = strategies.integers(min_value=0)
tag_number = strategies.one_of(
    strategies.integers(
        min_value=1, max_value=FieldDescriptor.FIRST_RESERVED_FIELD_NUMBER - 1,
    ),
    strategies.integers(
        min_value=FieldDescriptor.LAST_RESERVED_FIELD_NUMBER + 1,
        max_value=FieldDescriptor.MAX_FIELD_NUMBER,
    ),
)
field_types_and_values = strategies.one_of(
    type_with_value(strategies.booleans(), FieldDescriptor.TYPE_BOOL),
    type_with_value(strategies.binary(), FieldDescriptor.TYPE_BYTES),
    type_with_value(strategies.text(), FieldDescriptor.TYPE_STRING),
    type_with_value(strategies.floats(), FieldDescriptor.TYPE_DOUBLE),
    type_with_value(
        strategies.floats().map(lambda number : c_float(number).value),
        FieldDescriptor.TYPE_FLOAT,
    ),
    type_with_value(
        strategies.integers(min_value=-2 ** 31 + 1, max_value=2 ** 31 - 1),
        FieldDescriptor.TYPE_INT32,
        FieldDescriptor.TYPE_SFIXED32,
        FieldDescriptor.TYPE_SINT32,
    ),
    type_with_value(
        strategies.integers(min_value=-2 ** 63 + 1, max_value=2 ** 63 - 1),
        FieldDescriptor.TYPE_INT64,
        FieldDescriptor.TYPE_SFIXED64,
        FieldDescriptor.TYPE_SINT64,
    ),
    type_with_value(
        strategies.integers(min_value=0, max_value=2 ** 32 - 1),
        FieldDescriptor.TYPE_FIXED32,
        FieldDescriptor.TYPE_UINT32,
    ),
    type_with_value(
        strategies.integers(min_value=0, max_value=2 ** 64 - 1),
        FieldDescriptor.TYPE_FIXED64,
        FieldDescriptor.TYPE_UINT64,
    ),
    # type_with_value(FieldDescriptor.TYPE_GROUP,
    # type_with_value(FieldDescriptor.TYPE_MESSAGE,
    # type_with_value(FieldDescriptor.TYPE_ENUM,
)
def to_field_descriptor_and_value((type, value), **kwargs):
    # I have no idea why this part is my responsibility.
    cpp_type = FieldDescriptor.ProtoTypeToCppProtoType(type)
    return FieldDescriptor(type=type, cpp_type=cpp_type, **kwargs), value


label = strategies.just(FieldDescriptor.LABEL_OPTIONAL)
default_value = strategies.none()
field_and_value = strategies.builds(
    to_field_descriptor_and_value,
    field_types_and_values,
    name=strategies.binary(),
    full_name=full_name,
    index=index,
    number=tag_number,
    label=label,
    default_value=default_value,
    message_type=strategies.none(),
    enum_type=strategies.none(),
    containing_type=strategies.none(),
    is_extension=strategies.just(False),
    extension_scope=strategies.none(),
)


def to_descriptor_and_values(fields_and_values, **kwargs):
    fields, values = [], {}
    for field, value in fields_and_values:
        fields.append(field)
        values[field.name] = value
    return Descriptor(fields=fields, **kwargs), values


descriptor_and_values = strategies.builds(
    to_descriptor_and_values,
    fields_and_values=strategies.lists(
        field_and_value, unique_by=lambda (field, _) : field.number,
    ),
    name=strategies.binary(min_size=1),
    full_name=full_name,
    containing_type=strategies.none(),  # TODO: strategies.recursive?
    filename=strategies.none(),
    nested_types=strategies.just([]),
    enum_types=strategies.just([]),
    extensions=strategies.just([]),
)


def to_Message_and_arguments((descriptor, values)):
    return reflection.MakeClass(descriptor), values


Message_and_arguments = strategies.builds(
    to_Message_and_arguments, descriptor_and_values,
)


def to_message((Message, arguments)):
    message = Message()
    for attr, value in arguments.iteritems():
        setattr(message, attr, value)
    return message


message = strategies.builds(to_message, Message_and_arguments)
