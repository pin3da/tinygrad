#!/usr/bin/env python
import unittest
import numpy as np
from extra.utils import WINDOWS
from tinygrad.helpers import getenv
from tinygrad.jit import TinyJit
from tinygrad.tensor import Tensor, Device
from tinygrad.nn import BatchNorm2d, Conv1d, ConvTranspose1d, Conv2d, ConvTranspose2d, Linear, GroupNorm, LayerNorm, LayerNorm2d, Embedding, InstanceNorm
import torch
import pytest

pytestmark = [pytest.mark.exclude_cuda, pytest.mark.webgpu]

class TestNN(unittest.TestCase):

  def test_batchnorm2d(self, training=False):
    szs = [4, 8, 16, 32]
    for sz in szs:
      # create in tinygrad
      Tensor.training = training
      bn = BatchNorm2d(sz, eps=1e-5, track_running_stats=training)
      bn.weight = Tensor.randn(sz)
      bn.bias = Tensor.randn(sz)
      bn.running_mean = Tensor.randn(sz)
      bn.running_var = Tensor.randn(sz)
      bn.running_var.numpy()[bn.running_var.numpy() < 0] = 0

      # create in torch
      with torch.no_grad():
        tbn = torch.nn.BatchNorm2d(sz).eval()
        tbn.training = training
        tbn.weight[:] = torch.tensor(bn.weight.numpy())
        tbn.bias[:] = torch.tensor(bn.bias.numpy())
        tbn.running_mean[:] = torch.tensor(bn.running_mean.numpy())
        tbn.running_var[:] = torch.tensor(bn.running_var.numpy())

      np.testing.assert_allclose(bn.running_mean.numpy(), tbn.running_mean.detach().numpy(), rtol=1e-5, atol=1e-6)
      np.testing.assert_allclose(bn.running_var.numpy(), tbn.running_var.detach().numpy(), rtol=1e-5, atol=1e-6)

      # trial
      inn = Tensor.randn(2, sz, 3, 3)

      # in tinygrad
      outt = bn(inn)

      # in torch
      toutt = tbn(torch.tensor(inn.cpu().numpy()))

      # close
      np.testing.assert_allclose(outt.numpy(), toutt.detach().numpy(), rtol=5e-4, atol=1e-6)

      np.testing.assert_allclose(bn.running_mean.numpy(), tbn.running_mean.detach().numpy(), rtol=1e-5, atol=1e-6)

      np.testing.assert_allclose(bn.running_var.numpy(), tbn.running_var.detach().numpy(), rtol=1e-5, atol=1e-6)

  def test_batchnorm2d_training(self):
    self.test_batchnorm2d(True)

  def test_linear(self):
    def _test_linear(x):

      # create in tinygrad
      model = Linear(in_dim, out_dim)
      z = model(x)

      # create in torch
      with torch.no_grad():
        torch_layer = torch.nn.Linear(in_dim, out_dim).eval()
        torch_layer.weight[:] = torch.tensor(model.weight.numpy(), dtype=torch.float32)
        torch_layer.bias[:] = torch.tensor(model.bias.numpy(), dtype=torch.float32)
        torch_x = torch.tensor(x.cpu().numpy(), dtype=torch.float32)
        torch_z = torch_layer(torch_x)

      # test
      np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-4, rtol=1e-5)

    BS, T, in_dim, out_dim = 4, 2, 8, 16
    _test_linear(Tensor.randn(BS, in_dim))
    _test_linear(Tensor.randn(BS, T, in_dim)) # test with more dims

  def test_conv1d(self):
    BS, C1, W = 4, 16, 224
    C2, K, S, P = 64, 7, 2, 1

    # create in tinygrad
    layer = Conv1d(C1, C2, kernel_size=K, stride=S, padding=P)

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.Conv1d(C1, C2, kernel_size=K, stride=S, padding=P).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.uniform(BS, C1, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-4, rtol=1e-5)

  def test_conv2d(self):
    BS, C1, H, W = 4, 16, 224, 224
    C2, K, S, P = 64, 7, 2, 1

    # create in tinygrad
    layer = Conv2d(C1, C2, kernel_size=K, stride=S, padding=P)

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.Conv2d(C1, C2, kernel_size=K, stride=S, padding=P).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.uniform(BS, C1, H, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-4, rtol=1e-5)

  @unittest.skipIf(getenv("CI", "") != "" and (WINDOWS or Device.DEFAULT == "WEBGPU"), "runs out of memory in CI")
  def test_conv_transpose1d(self):
    BS, C1, W = 4, 16, 224
    C2, K, S, P = 64, 7, 2, 1

    # create in tinygrad
    layer = ConvTranspose1d(C1, C2, kernel_size=K, stride=S, padding=P)

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.ConvTranspose1d(C1, C2, kernel_size=K, stride=S, padding=P).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.uniform(BS, C1, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-4, rtol=1e-5)

  @unittest.skipIf(getenv("CI", "") != "" and (WINDOWS or Device.DEFAULT == "WEBGPU"), "runs out of memory in CI")
  def test_conv_transpose2d(self):
    BS, C1, H, W = 4, 16, 224, 224
    C2, K, S, P = 64, 7, 2, 1

    # create in tinygrad
    layer = ConvTranspose2d(C1, C2, kernel_size=K, stride=S, padding=P)

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.ConvTranspose2d(C1, C2, kernel_size=K, stride=S, padding=P).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.uniform(BS, C1, H, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-4, rtol=1e-5)

  def test_groupnorm(self):
    BS, H, W, C, G = 20, 10, 10, 6, 3

    # create in tinygrad
    layer = GroupNorm(G, C)

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.GroupNorm(G, C).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.randn(BS, C, H, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-3, rtol=5e-3)

  def test_layernorm(self):
    N, C, H, W = 20, 5, 10, 10

    # create in tinygrad
    layer = LayerNorm([H, W])

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.LayerNorm([H, W]).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.randn(N, C, H, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-3, rtol=5e-3)

  def test_layernorm_2d(self):
    N, C, H, W = 20, 5, 10, 10

    # create in tinygrad
    layer = LayerNorm2d(C)

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.LayerNorm([C]).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.randn(N, C, H, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x.permute(0,2,3,1)).permute(0,3,1,2)

  def test_instancenorm_2d(self):
    N, C, H, W = 20, 5, 10, 10

    # create in tinygrad
    layer = InstanceNorm(C)

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.InstanceNorm2d(C, affine=True).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.randn(N, C, H, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-3, rtol=5e-3)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-3, rtol=5e-3)

  def test_instancenorm_3d(self):
    N, C, D, H, W = 20, 5, 3, 10, 10

    # create in tinygrad
    layer = InstanceNorm(C)

    # create in torch
    with torch.no_grad():
      torch_layer = torch.nn.InstanceNorm3d(C, affine=True).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)
      torch_layer.bias[:] = torch.tensor(layer.bias.numpy(), dtype=torch.float32)

    # test
    x = Tensor.randn(N, C, D, H, W)
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy())
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-3, rtol=5e-3)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=5e-3, rtol=5e-3)

  def test_embedding(self):
    B, T, C, VS = 4, 10, 20, 28

    # create in tinygrad
    layer = Embedding(VS, C)

    with torch.no_grad():
      torch_layer = torch.nn.Embedding(VS, C).eval()
      torch_layer.weight[:] = torch.tensor(layer.weight.numpy(), dtype=torch.float32)

    # test
    x = Tensor(np.random.randint(0, VS, (B, T)).astype(np.float32))
    z = layer(x)
    torch_x = torch.tensor(x.cpu().numpy().astype(np.int32))
    torch_z = torch_layer(torch_x)
    np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=1e-8, rtol=1e-8)

    # test with jit enabled
    @TinyJit
    def layer_jit(x):
      return layer(x).realize()

    for _ in range(3):
      x = Tensor(np.random.randint(0, VS, (B, T)).astype(np.float32))
      z = layer_jit(x)
      torch_x = torch.tensor(x.cpu().numpy().astype(np.int32))
      torch_z = torch_layer(torch_x)
      np.testing.assert_allclose(z.numpy(), torch_z.detach().numpy(), atol=1e-8, rtol=1e-8)


if __name__ == '__main__':
  unittest.main()
