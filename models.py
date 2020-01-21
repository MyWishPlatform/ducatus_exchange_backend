import marshmallow


class Address(marshmallow.Schema):
    id = marshmallow.fields.Int(dump_only=True)
    address = marshmallow.fields.String()