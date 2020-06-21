import torch
import torch.nn as nn
import torch.nn.functional as f
import torch.optim as optim

from PIL import Image
import torchvision.transforms as transforms
import copy
import torchvision.models as models


# Loss content image
class ContentLoss(nn.Module):
    def __init__(self, target):
        super(ContentLoss, self).__init__()
        self.target = target.detach()

    def forward(self, input):
        self.loss = f.mse_loss(input, self.target)
        return input

# Loss style image
class StyleLoss(nn.Module):
    def __init__(self, target_features, instance):
        super(StyleLoss, self).__init__()
        self.instance = instance
        self.target = self.instance.gram_matrix(target_features).detach()

    def forward(self, input):
        G = self.instance.gram_matrix(input)
        self.loss = (f.mse_loss(G, self.target))
        return input

class Normalization(nn.Module):
    def __init__(self, mean, std):
        super(Normalization, self).__init__()
        self.mean = torch.tensor(mean).view(-1, 1, 1)
        self.std = torch.tensor(std).view(-1, 1, 1)

    def forward(self, img):
        return (img - self.mean) / self.std

class StyleTransfer:
    def __init__(self, style_image, content_image):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.n = Image.open(content_image).size[0]/Image.open(content_image).size[1]
        self.style_img = self.image_loader(style_image)
        self.content_img = self.image_loader(content_image)
        self.cnn = models.vgg19(pretrained=True).features.to(self.device).eval()
        self.cnn_normalization_mean = torch.tensor([0.485, 0.456, 0.406]).to(self.device)
        self.cnn_normalization_std = torch.tensor([0.229, 0.224, 0.225]).to(self.device)
        self.content_layers_default = ['conv_1']
        self.style_layers_default = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']


    def image_loader(self, img_path, size=256):
        image = Image.open(img_path).convert('RGB')

        loader = transforms.Compose([
            transforms.Resize((size, int(self.n*size))),
            transforms.ToTensor()])

        image = loader(image).unsqueeze(0)
        return image.to(self.device, torch.float)

    def gram_matrix(self, input):
        a, b, c, d = input.size()
        features = input.view(a * b, c * d)

        G = torch.mm(features, features.t())
        return G.div(a * b * c * d)

    def get_style_model_and_losses(self, cnn, normalization_mean, normalization_std,
                                   content_image, style_image,
                                   content_layers=None,
                                   style_layers=None):
        if content_layers is None:
            content_layers = self.content_layers_default
        if style_layers is None:
            style_layers = self.style_layers_default

        cnn = copy.deepcopy(cnn)
        normalization = Normalization(normalization_mean, normalization_std).to(self.device)

        content_losses = []
        style_losses = []

        model = nn.Sequential(normalization)

        i = 0
        for layer in cnn.children():
            if isinstance(layer, nn.Conv2d):
                i += 1
                name = 'conv_{}'.format(i)
            elif isinstance(layer, nn.ReLU):
                name = 'relu_{}'.format(i)
                layer = nn.ReLU(inplace=False)
            elif isinstance(layer, nn.MaxPool2d):
                name = 'pool_{}'.format(i)
            elif isinstance(layer, nn.BatchNorm2d):
                name = 'bn_{}'.format(i)
            else:
                raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

            model.add_module(name, layer)

            if name in content_layers:
                target = model(content_image).detach()
                content_loss = ContentLoss(target)
                model.add_module('content_loss{}'.format(i), content_loss)
                content_losses.append(content_loss)

            if name in style_layers:
                target = model(style_image).detach()
                style_loss = StyleLoss(target, self)
                model.add_module('style_loss{}'.format(i), style_loss)
                style_losses.append(style_loss)

        for i in range(len(model) - 1, -1, -1):
            if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLoss):
                break

        model = model[:(i + 1)]

        return model, content_losses, style_losses

    def get_input_optimizer(self, input_img):
        optimizer = optim.LBFGS([input_img.requires_grad_()])
        return optimizer

    def run_style_transfer(self, cnn, normalization_mean, normalization_std,
                           content_image, style_image, input_img,
                           num_steps=100, style_weight=1000, content_weight=1):

        model, content_losses, style_losses = self.get_style_model_and_losses(cnn, normalization_mean, normalization_std,
                                                                            content_image, style_image)

        optimizer = self.get_input_optimizer(input_img)

        run = [0]
        while run[0] <= num_steps:
            def closure():
                input_img.data.clamp_(0, 1)

                optimizer.zero_grad()
                model(input_img)
                style_score = 0
                content_score = 0

                for sl in style_losses:
                    style_score += sl.loss
                for cl in content_losses:
                    content_score += cl.loss

                style_score *= style_weight
                content_score *= content_weight

                loss = style_score + content_score
                loss.backward()

                run[0] += 1
                if run[0] % 50 == 0:
                    print("run {}:".format(run))
                    print('Style Loss : {:4f} Content Loss: {:4f}'.format(
                        style_score.item(), content_score.item()))
                    print()

                return style_score + content_score

            optimizer.step(closure)

        input_img.data.clamp_(0, 1)

        return input_img

    def get_output(self):
        input_img = self.content_img.detach()
        output_img = self.run_style_transfer(self.cnn, self.cnn_normalization_mean, self.cnn_normalization_std,
                                             self.content_img, self.style_img, input_img)

        unloader = transforms.ToPILImage(mode='RGB')
        image = output_img.cpu().clone()
        image = image.squeeze(0)
        image = unloader(image)

        return image


