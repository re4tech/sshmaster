import json
from typing import Dict, Type

from pony.orm.core import Attribute, EntityMeta
from pydantic import BaseConfig, BaseModel, Field, Json, create_model, validator

import config
from models import Port, SSH


def generate_pydantic_model(entity: Type[EntityMeta], model_name, field_description: Dict[str, str]):
    class Config(BaseConfig):
        orm_mode = True

    entity_name = repr(entity.__name__)
    model_fields = {}
    relationship_fields = []
    description_missing = []

    entity_attr: Attribute
    # noinspection PyProtectedMember,PyArgumentList
    for entity_attr in entity._get_attrs_(exclude=['classtype']):
        if entity_attr.is_relation:
            attr_type = Json
            relationship_fields.append(entity_attr.name)
        else:
            attr_type = entity_attr.py_type

        field_args = {}
        if not entity_attr.is_required:
            field_args['default'] = None
        if entity_attr.kwargs.get('min'):
            field_args['ge'] = entity_attr.kwargs['min']
        if entity_attr.kwargs.get('max'):
            field_args['le'] = entity_attr.kwargs['max']

        if entity_attr.name in field_description:
            field_args['description'] = field_description[entity_attr.name]
        else:
            description_missing.append(entity_attr.name)

        model_fields[entity_attr.name] = (attr_type, Field(**field_args))

    # Raise exception for missing/redundant description
    # (to ensure programmer won't forget to change them after updating the model)
    if description_missing:
        missing_display = ', '.join(map(repr, description_missing))
        print(json.dumps({i: '' for i in description_missing}, indent=4))
        raise KeyError(f"No description found of entity {entity_name} for attributes: {missing_display}")

    if redundant_fields := set(field_description) - set(model_fields):
        redundant_display = ', '.join(map(repr, redundant_fields))
        raise KeyError(f"Redundant description found of entity {entity_name} for attributes: {redundant_display}")

    # noinspection PyUnusedLocal
    @validator(*relationship_fields, pre=True, always=True, allow_reuse=True)
    def relationship_validator(cls, v):
        if v:
            if isinstance(v, dict):
                data = v
            else:
                data = v.to_dict()
            return json.dumps(data, default=str)

    return create_model(model_name,
                        __config__=Config,
                        __validators__={'relationship_validator': relationship_validator},
                        **model_fields)


class SSHIn(BaseModel):
    ip: str
    username: str = None
    password: str = None
    port: int = None


SSHOutBase = generate_pydantic_model(SSH, 'SSHOutBase', {
    "id": "",
    "last_checked": "Th???i ??i???m ???????c ki???m tra g???n nh???t",
    "last_modified": "Th???i ??i???m c???p nh???t g???n nh???t",
    "ip": "IP c???a SSH",
    "username": "Username c???a SSH",
    "password": "M???t kh???u ????ng nh???p SSH",
    "ssh_port": "Port k???t n???i v??o SSH (v?? d???: 22)",
    "is_live": "SSH live v?? s??? d???ng ???????c",
    "port": "ID c???a Port m?? SSH n??y g??n v??o"
})


class SSHOut(SSHOutBase):
    status_text: str = None

    # noinspection PyMethodParameters
    @validator('status_text', pre=True, always=True, check_fields=False)
    def default_status_text(cls, v, values):
        if v:
            return v
        return {
            True: 'live',
            False: 'die'
        }.get(values['is_live'], '')


class PortIn(BaseModel):
    port_number: int


PortOut = generate_pydantic_model(Port, 'PortOut', {
    "id": "",
    "last_checked": "Th???i ??i???m Port ???????c ki???m tra g???n nh???t",
    "last_modified": "Th???i ??i???m Port ???????c c???p nh???t g???n nh???t",
    "port_number": "C???ng trong m??y local ???????c qu???n l?? b???i Port",
    "auto_connect": "T??? ?????ng k???t n???i SSH ?????n Port",
    "ssh": "ID c???a SSH ???????c s??? d???ng cho Port",
    "is_connected": "Port ???? ???????c k???t n???i ?????n SSH",
    "public_ip": "IP b??n ngo??i c???a proxy t??? Port",
    "time_connected": "Th???i ??i???m Port k???t n???i ?????n SSH",
    "proxy_address": "?????a ch??? proxy c???a Port",
    "is_working": "C?? task ??ang ???????c th???c thi tr??n Port",
})

SettingsInOut = create_model('SettingsInOut', **config.PYDANTIC_ARGS)


class SettingsUpdateResult(BaseModel):
    need_restart: bool
