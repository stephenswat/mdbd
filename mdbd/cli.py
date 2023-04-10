import typer
import pathlib
import rich
import tomllib
import pydantic
import os
import io
import threading
import base64
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import StreamDeck.DeviceManager
import StreamDeck.ImageHelpers.PILHelper

import mdbd.schema.configuration


cli = typer.Typer(
    help="mdbd is an ambiance manager for Elgato Stream Decks."
)


@cli.command()
def devices():
    dev_manager = StreamDeck.DeviceManager.DeviceManager()



    for i, d in enumerate(dev_manager.enumerate()):
        # rich.print(str(i))

        image_format = d.key_image_format()

        flip_description = {
            (False, False): "not mirrored",
            (True, False): "mirrored horizontally",
            (False, True): "mirrored vertically",
            (True, True): "mirrored horizontally/vertically",
        }

        print("Deck {} - {}.".format(i, d.deck_type()))
        print("\t - ID: {}".format(d.id()))
        # print("\t - Serial: '{}'".format(d.get_serial_number()))
        # print("\t - Firmware Version: '{}'".format(d.get_firmware_version()))
        print("\t - Key Count: {} (in a {}x{} grid)".format(
            d.key_count(),
            d.key_layout()[0],
            d.key_layout()[1]))
        if d.is_visual():
            print("\t - Key Images: {}x{} pixels, {} format, rotated {} degrees, {}".format(
                image_format['size'][0],
                image_format['size'][1],
                image_format['format'],
                image_format['rotation'],
                flip_description[image_format['flip']]))
        else:
            print("\t - No Visual Output")



# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck, label_text, icon):
    image = StreamDeck.ImageHelpers.PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 0, 0])

    print(image.width, image.height)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = PIL.ImageDraw.Draw(image)
    font = PIL.ImageFont.truetype("/home/stephen/Projects/mdbd/mdbd/fonts/Roboto-Regular.ttf", 14)
    draw.text((image.width / 2, image.height - 10), text=label_text, anchor="ms", fill="white", font=font, stroke_fill="black", stroke_width=2)

    return StreamDeck.ImageHelpers.PILHelper.to_native_format(deck, image)


def update_key_image(deck, key, text, icon):
    # Generate the custom key with the requested image and label.

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        image = render_key_image(deck, text, icon)
        # Update requested key with the generated image.
        deck.set_key_image(key, image)

def load_image(comp):
    if type(comp) == mdbd.schema.configuration.Base64Image:
        return PIL.Image.open(io.BytesIO(base64.b64decode(comp.base64)))
    elif type(comp) == mdbd.schema.configuration.FileImage:
        with open(comp.path, "rb") as f:
            return PIL.Image.open(io.BytesIO(f.read()))


@cli.command()
def run(config: pathlib.Path, deck: str = None):
    dev_manager = StreamDeck.DeviceManager.DeviceManager()
    devices = dev_manager.enumerate()

    if deck is None:
        dev = devices[0]
    else:
        for d in devices:
            if d.id() == deck:
                dev = d
                break
        else:
            rich.print(f"[bold red]Error:[/] No device [bold yellow]{deck}[/] found. Try [bold cyan]mdbd devices[/].")
            raise typer.Exit(code=1)

    rich.print(f"[bold blue]Information:[/] Using device [bold yellow]{dev.id()}[/].")

    with open(config, "rb") as f:
        conf = mdbd.schema.configuration.Configuration(**tomllib.load(f))

    rich.print(conf)

    dev.open()

    try:
        with dev:
            dev.reset()
            dev.set_brightness(100)

        for i, e in enumerate(conf.environments.values()):
            update_key_image(dev, i, e.name, load_image(conf.components.images[e.icon]))

        dev.close()
    except TransportError as e:
        print(e)
    finally:
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass


@cli.command()
def validate(config: pathlib.Path):
    with open(config, "rb") as f:
        cfg = tomllib.load(f)

    # rich.print(cfg)

    try:
        conf = mdbd.schema.configuration.Configuration(**cfg)
        rich.print(f"The configuration [magenta]{config}[/] is [bold green]valid[/].")
    except pydantic.ValidationError as e:
        rich.print(f"The configuration [magenta]{config}[/] is [bold red]invalid[/]:")
        
        for l in e.errors():
            rich.print(f"    [blue]{'.'.join(l['loc'])}[/]: [red]{l['msg']}[/]")

        raise typer.Exit(code=1)

    rich.print(conf)

@cli.callback()
def main():
    pass
