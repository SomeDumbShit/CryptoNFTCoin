from PIL import Image


# наложение атрибутов по слоям
def combine_layers(attributes):
    if not attributes:
        return None

    result_image = Image.open(attributes[0]).convert("RGBA")

    for path in attributes[1:]:
        if 'none' in path: continue
        layer = Image.open(path).convert("RGBA")
        result_image = Image.alpha_composite(result_image, layer)

    return result_image


def art_by_image_path(image_path):
    background, body, eyes, ears, mouth, clothes, hats, accessory = image_path.split('_')
    paths = [
        f'app/static/attributes/background/{background}.png',
        f'app/static/attributes/body/{body}.png',
        f'app/static/attributes/eyes/{eyes}.png',
        f'app/static/attributes/ears/{ears}.png',
        f'app/static/attributes/clothes/{clothes}.png',
        f'app/static/attributes/mouth/{mouth}.png',
        f'app/static/attributes/hats/{hats}.png',
        f'app/static/attributes/accessories/{accessory}.png'
    ]