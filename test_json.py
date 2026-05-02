import json
from pydantic import BaseModel, ValidationError
class M(BaseModel):
    quantity: int
try:
    M(quantity="apple")
except ValidationError as e:
    try:
        json.dumps(e.errors())
        print("Success")
    except Exception as exc:
        print("Failed:", exc)
