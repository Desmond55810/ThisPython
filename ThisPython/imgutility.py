from PIL import Image

from luminoth.tools.checkpoint import get_checkpoint_config
from luminoth.utils.predicting import PredictorNetwork

def predict(abspath):
    checkpoint = 'fast'
    config = get_checkpoint_config(checkpoint)
    network = PredictorNetwork(config)
    image = Image.open(abspath).convert('RGB')
    objects = network.predict_image(image)
    return objects
