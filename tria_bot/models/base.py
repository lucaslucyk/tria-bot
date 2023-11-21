
# models.py
from aredis_om import HashModel, JsonModel


class HashModelBase(HashModel):
    ...

    class Config:
        extra = "ignore"
        populate_by_name = True
        allow_population_by_field_name = True


class JsonModelBase(JsonModel):
    ...
    
    class Config:
        extra = "ignore"
        populate_by_name = True
        allow_population_by_field_name = True