# models.py
from aredis_om import HashModel


class ModelBase(HashModel):
    ...


class Customer(ModelBase):
    first_name: str
    last_name: str


    class Meta:
        model_key_prefix = "Customer"
        global_key_prefix = "tria_bot"