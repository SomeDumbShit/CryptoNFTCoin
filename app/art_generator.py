from PIL import Image


# наложение атрибутов по слоям
def combine_layers(attributes):
    if not attributes:
        return None

    result_image = Image.open(attributes[0]).convert("RGBA")

    for path in attributes[1:]:
        layer = Image.open(path).convert("RGBA")
        result_image = Image.alpha_composite(result_image, layer)

    return result_image
