'''
2025/04/11
----------
Author: Sherry
'''
import torch
import torchvision.transforms as transforms
from PIL import Image
from torchvision.models import resnet18
import numpy as np
# import的路徑請用相對路徑

def get_model(weight_path='classification/resnet18-f37072fd.pth', device='cpu'):
    """
    Obtain the model with pre-load trained weight.

    Parameters
    ----------
    device: The device used to run the model

    returns
    ----------
    model: The classification model that can be used for prediction.

    Examples:
    --------
    >>> device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    >>> model = get_cls_model(device)
    """
    classifi_model = resnet18(pretrained=False).to(device)
    classifi_model.load_state_dict(torch.load(weight_path, weights_only=True))

    return classifi_model

def preprocess(image):
    classifi_transform = transforms.Compose(
        [
            transforms.Resize(
                (384, 384)
            ),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ]
    )

    image = classifi_transform(image).unsqueeze(0)

    return image


def classification(img:torch.Tensor, model, device='cpu'):  # for predicting one image
    '''
    Return the classification result.

    Parameters
    ----------
    img: The image after preprocess. Its shape is (1,c,h,w).

    model: The model.

    device: The device used to run the model

    returns
    ----------
    prediction: int      

    Examples
    --------
    >>> prediction = classification(img, model, device)
    >>> print(prediction)
    '''
    img = img.to(device)

    model.eval()
    
    with torch.no_grad():
        output = model(img)
        pred = torch.max(output, 1)

    return pred

def batch_classification(imgs, model, device='cpu'):

    imgs = imgs.to(device)

    model.eval()

    with torch.no_grad():

        outputs = model(imgs)
        _, preds = torch.max(outputs, 1)
        preds = preds.tolist()

    probs = torch.nn.functional.softmax(outputs, dim=1)

    indices = torch.arange(probs.shape[0])
    probs = probs[indices, preds].cpu().numpy().tolist()

    return preds, probs


