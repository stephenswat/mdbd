import pydantic
import typing
import pathlib
import enum


class ImageMIME(str, enum.Enum):
    PNG = 'image/png'
    JPEG = 'image/jpeg'


class Action(pydantic.BaseModel):
    name: str
    icon: str

    class Config:
        extra = pydantic.Extra.forbid


class Base64Image(pydantic.BaseModel):
    mime: ImageMIME
    base64: str

    class Config:
        extra = pydantic.Extra.forbid


class FileImage(pydantic.BaseModel):
    mime: ImageMIME
    path: pathlib.Path

    class Config:
        extra = pydantic.Extra.forbid


class HueLight(pydantic.BaseModel):
    interface: typing.Literal["hue"]

    class Config:
        extra = pydantic.Extra.forbid


Image = typing.Union[Base64Image, FileImage]

Light = typing.Union[HueLight]

class Playlist(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

class Sound(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid


class Components(pydantic.BaseModel):
    images: dict[str, Image]
    lights: dict[str, Light]
    sounds: dict[str, Sound]
    playlists: dict[str, Playlist]

    class Config:
        extra = pydantic.Extra.forbid


class Environment(pydantic.BaseModel):
    name: str
    icon: str

    actions: list[str] = []

    on_entry: list[str] | None
    on_exit: list[str] | None

    class Config:
        extra = pydantic.Extra.forbid


class Configuration(pydantic.BaseModel):
    title: str

    components: Components

    actions: dict[str, Action]

    environments: dict[str, Environment]

    class Config:
        extra = pydantic.Extra.forbid
