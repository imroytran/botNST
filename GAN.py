# source https://github.com/Yijunmaverick/CartoonGAN-Test-Pytorch-Torch


import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import numpy as np
from PIL import Image
import torchvision.transforms as transforms



class InstanceNormalization(nn.Module):
    def __init__(self, dim, eps=1e-9):
        super(InstanceNormalization, self).__init__()
        self.scale = nn.Parameter(torch.FloatTensor(dim))
        self.shift = nn.Parameter(torch.FloatTensor(dim))
        self.eps = eps
        self._reset_parameters()

    def _reset_parameters(self):
        self.scale.data.uniform_()
        self.shift.data.zero_()

    def __call__(self, x):
        n = x.size(2) * x.size(3)
        t = x.view(x.size(0), x.size(1), n)
        mean = torch.mean(t, 2).unsqueeze(2).unsqueeze(3).expand_as(x)
        # Calculate the biased var. torch.var returns unbiased var
        var = torch.var(t, 2).unsqueeze(2).unsqueeze(3).expand_as(x) * ((n - 1) / float(n))
        scale_broadcast = self.scale.unsqueeze(1).unsqueeze(1).unsqueeze(0)
        scale_broadcast = scale_broadcast.expand_as(x)
        shift_broadcast = self.shift.unsqueeze(1).unsqueeze(1).unsqueeze(0)
        shift_broadcast = shift_broadcast.expand_as(x)
        out = (x - mean) / torch.sqrt(var + self.eps)
        out = out * scale_broadcast + shift_broadcast
        return out
"""
class Refpad_block(nn.Module):
    def __init__(self, in_chanels, out_chanels, kernel_size, padding, out=True):
        super().__init__()
        module = [
            nn.ReflectionPad2d(padding),
            nn.Conv2d(in_chanels, out_chanels, kernel_size)
        ]
        if out:
            module.append(InstanceNormalization(out_chanels))

        self.refpad = nn.Sequential(*module)

    def forward(self, x):
        return self.refpad(x)


class Conv_block(nn.Module):
    def __init__(self, in_chanels, out_chanels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_chanels, out_chanels, 3, 2, 1),
            nn.Conv2d(out_chanels, out_chanels, 3, 2, 1),
            InstanceNormalization(out_chanels)
        )

    def forward(self, x):
        x = self.conv(x)
        return F.relu(x)

class Deconv_block(nn.Module):
    def __init__(self, in_chanels, out_chanels):
        super().__init__()
        self.deconv = nn.Sequential(
            nn.ConvTranspose2d(in_chanels, out_chanels, 3, 2, 1, 1),
            nn.Conv2d(out_chanels, out_chanels, 3, 2, 1, 1),
            InstanceNormalization(out_chanels)
        )

    def forward(self, x):
        x = self.deconv(x)
        return F.relu(x)


class GanCartoon(nn.Module):
    def __init__(self):
        super(GanCartoon, self).__init__()
        self.refpad01 = Refpad_block(3, 64, 7, 3)

        self.conv01 = Conv_block(64, 128)
        self.conv02 = Conv_block(128, 256)

        self.refpad_mid = Refpad_block(256, 256, 3, 1)

        self.deconv01 = Deconv_block(256, 128)
        self.deconv02 = Deconv_block(128, 64)

        self.refpad02  = Refpad_block(64, 3, 7, 3, out=False)

    def forward(self, x):
        t1 = self.conv02(self.conv01(F.relu(self.refpad01(x))))

        t2 = self.refpad_mid(F.relu(self.refpad_mid(t1))) + t1

        t3 = self.refpad_mid(F.relu(self.refpad_mid(t2))) + t2

        t4 = self.refpad_mid(F.relu(self.refpad_mid(t3))) + t3

        t5 = self.refpad_mid(F.relu(self.refpad_mid(t4))) + t4

        t6 = self.refpad_mid(F.relu(self.refpad_mid(t5))) + t5

        t7 = self.refpad_mid(F.relu(self.refpad_mid(t6))) + t6

        t8 = self.refpad_mid(F.relu(self.refpad_mid(t7))) + t7

        t9 = self.refpad_mid(F.relu(self.refpad_mid(t8))) + t8

        y = F.tanh(self.refpad02(self.deconv02(self.deconv01(t9))))

        return y

"""

class GanCartoon(nn.Module):
    def __init__(self):
        super(GanCartoon, self).__init__()

        self.refpad01_1 = nn.ReflectionPad2d(3)
        self.conv01_1 = nn.Conv2d(3, 64, 7)
        self.in01_1 = InstanceNormalization(64)

        self.conv02_1 = nn.Conv2d(64, 128, 3, 2, 1)
        self.conv02_2 = nn.Conv2d(128, 128, 3, 1, 1)
        self.in02_1 = InstanceNormalization(128)

        self.conv03_1 = nn.Conv2d(128, 256, 3, 2, 1)
        self.conv03_2 = nn.Conv2d(256, 256, 3, 1, 1)
        self.in03_1 = InstanceNormalization(256)

        ## res block 1
        self.refpad04_1 = nn.ReflectionPad2d(1)
        self.conv04_1 = nn.Conv2d(256, 256, 3)
        self.in04_1 = InstanceNormalization(256)

        self.refpad04_2 = nn.ReflectionPad2d(1)
        self.conv04_2 = nn.Conv2d(256, 256, 3)
        self.in04_2 = InstanceNormalization(256)


        ## res block 2
        self.refpad05_1 = nn.ReflectionPad2d(1)
        self.conv05_1 = nn.Conv2d(256, 256, 3)
        self.in05_1 = InstanceNormalization(256)

        self.refpad05_2 = nn.ReflectionPad2d(1)
        self.conv05_2 = nn.Conv2d(256, 256, 3)
        self.in05_2 = InstanceNormalization(256)


        ## res block 3
        self.refpad06_1 = nn.ReflectionPad2d(1)
        self.conv06_1 = nn.Conv2d(256, 256, 3)
        self.in06_1 = InstanceNormalization(256)

        self.refpad06_2 = nn.ReflectionPad2d(1)
        self.conv06_2 = nn.Conv2d(256, 256, 3)
        self.in06_2 = InstanceNormalization(256)


        ## res block 4
        self.refpad07_1 = nn.ReflectionPad2d(1)
        self.conv07_1 = nn.Conv2d(256, 256, 3)
        self.in07_1 = InstanceNormalization(256)

        self.refpad07_2 = nn.ReflectionPad2d(1)
        self.conv07_2 = nn.Conv2d(256, 256, 3)
        self.in07_2 = InstanceNormalization(256)


        ## res block 5
        self.refpad08_1 = nn.ReflectionPad2d(1)
        self.conv08_1 = nn.Conv2d(256, 256, 3)
        self.in08_1 = InstanceNormalization(256)

        self.refpad08_2 = nn.ReflectionPad2d(1)
        self.conv08_2 = nn.Conv2d(256, 256, 3)
        self.in08_2 = InstanceNormalization(256)


        ## res block 6
        self.refpad09_1 = nn.ReflectionPad2d(1)
        self.conv09_1 = nn.Conv2d(256, 256, 3)
        self.in09_1 = InstanceNormalization(256)

        self.refpad09_2 = nn.ReflectionPad2d(1)
        self.conv09_2 = nn.Conv2d(256, 256, 3)
        self.in09_2 = InstanceNormalization(256)


        # res block 7
        self.refpad10_1 = nn.ReflectionPad2d(1)
        self.conv10_1 = nn.Conv2d(256, 256, 3)
        self.in10_1 = InstanceNormalization(256)

        self.refpad10_2 = nn.ReflectionPad2d(1)
        self.conv10_2 = nn.Conv2d(256, 256, 3)
        self.in10_2 = InstanceNormalization(256)


        ## res block 8
        self.refpad11_1 = nn.ReflectionPad2d(1)
        self.conv11_1 = nn.Conv2d(256, 256, 3)
        self.in11_1 = InstanceNormalization(256)

        self.refpad11_2 = nn.ReflectionPad2d(1)
        self.conv11_2 = nn.Conv2d(256, 256, 3)
        self.in11_2 = InstanceNormalization(256)



        self.deconv01_1 = nn.ConvTranspose2d(256, 128, 3, 2, 1, 1)
        self.deconv01_2 = nn.Conv2d(128, 128, 3, 1, 1)
        self.in12_1 = InstanceNormalization(128)

        self.deconv02_1 = nn.ConvTranspose2d(128, 64, 3, 2, 1, 1)
        self.deconv02_2 = nn.Conv2d(64, 64, 3, 1, 1)
        self.in13_1 = InstanceNormalization(64)

        self.refpad12_1 = nn.ReflectionPad2d(3)
        self.deconv03_1 = nn.Conv2d(64, 3, 7)


    def forward(self, x):
        y = F.relu(self.in01_1(self.conv01_1(self.refpad01_1(x))))
        y = F.relu(self.in02_1(self.conv02_2(self.conv02_1(y))))
        t04 = F.relu(self.in03_1(self.conv03_2(self.conv03_1(y))))

        ##
        y = F.relu(self.in04_1(self.conv04_1(self.refpad04_1(t04))))
        t05 = self.in04_2(self.conv04_2(self.refpad04_2(y))) + t04

        y = F.relu(self.in05_1(self.conv05_1(self.refpad05_1(t05))))
        t06 = self.in05_2(self.conv05_2(self.refpad05_2(y))) + t05

        y = F.relu(self.in06_1(self.conv06_1(self.refpad06_1(t06))))
        t07 = self.in06_2(self.conv06_2(self.refpad06_2(y))) + t06

        y = F.relu(self.in07_1(self.conv07_1(self.refpad07_1(t07))))
        t08 = self.in07_2(self.conv07_2(self.refpad07_2(y))) + t07

        y = F.relu(self.in08_1(self.conv08_1(self.refpad08_1(t08))))
        t09 = self.in08_2(self.conv08_2(self.refpad08_2(y))) + t08

        y = F.relu(self.in09_1(self.conv09_1(self.refpad09_1(t09))))
        t10 = self.in09_2(self.conv09_2(self.refpad09_2(y))) + t09

        y = F.relu(self.in10_1(self.conv10_1(self.refpad10_1(t10))))
        t11 = self.in10_2(self.conv10_2(self.refpad10_2(y))) + t10

        y = F.relu(self.in11_1(self.conv11_1(self.refpad11_1(t11))))
        y = self.in11_2(self.conv11_2(self.refpad11_2(y))) + t11
        ##

        y = F.relu(self.in12_1(self.deconv01_2(self.deconv01_1(y))))
        y = F.relu(self.in13_1(self.deconv02_2(self.deconv02_1(y))))
        y = torch.tanh(self.deconv03_1(self.refpad12_1(y)))

        return y

def get_output(style, image, load_size = 512):
    model = GanCartoon()
    model.load_state_dict(torch.load(os.path.join('models', style + '_net_G_float.pth')))
    model.eval()

    model.float()

    input_image = Image.open(image).convert('RGB')

    # resize image, keep aspect ratio
    h = input_image.size[0]
    w = input_image.size[1]
    ratio = h * 1.0 / w
    if ratio > 1:
        h = load_size
        w = int(h * 1.0 / ratio)
    else:
        w = load_size
        h = int(w * ratio)
    input_image = input_image.resize((h, w))
    input_image = np.asarray(input_image)

    # RGB -> BGR
    input_image = input_image[:, :, [2, 1, 0]]
    input_image = transforms.ToTensor()(input_image).unsqueeze(0)

    # preprocess, (-1, 1)
    input_image = -1 + 2 * input_image

    # forward
    with torch.no_grad():
        output_image = model(input_image)

    output_image = output_image[0]
    # BGR -> RGB
    output_image = output_image[[2, 1, 0], :, :]
    # deprocess, (0, 1)
    output_image = output_image.data.cpu().float() * 0.5 + 0.5

    return output_image

