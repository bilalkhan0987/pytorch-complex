import math
import numpy as np

import torch
from torch import Tensor

from torch.nn.parameter import Parameter
from torch.nn import ParameterList

class _tensorprocessor():
    @classmethod
    def _preprocess(cls, tensor):
        if type(tensor) is ParameterList:
            cls.complex_weight=False
            return tensor
        else:
            cls.complex_weight=True
            return ParameterList([Parameter(tensor.real), Parameter(tensor.imag)])
    @classmethod
    def _postprocess(cls, tensor):
        if cls.complex_weight:
            return Parameter(tensor[0] + 1j*tensor[1])
        else:
            return tensor if type(tensor) is ParameterList else ParameterList(tensor)

# These no_grad_* functions are necessary as wrappers around the parts of these
# functions that use `with torch.no_grad()`. The JIT doesn't support context
# managers, so these need to be implemented as builtins. Using these wrappers
# lets us keep those builtins small and re-usable.
def _no_grad_uniform_(tensor, a, b):
    with torch.no_grad():
        return (tensor[0].uniform_(a, b), tensor[1].uniform_(a, b))


def _no_grad_normal_(tensor, mean, std):
    with torch.no_grad():
        return (tensor[0].normal_(mean, std), tensor[1].normal_(mean, std))


# def _no_grad_trunc_normal_(tensor, mean, std, a, b):
#     # Method based on https://people.sc.fsu.edu/~jburkardt/presentations/truncated_normal.pdf
#     def norm_cdf(x):
#         # Computes standard normal cumulative distribution function
#         return (1. + math.erf(x / math.sqrt(2.))) / 2.

#     if (mean < a - 2 * std) or (mean > b + 2 * std):
#         warnings.warn("mean is more than 2 std from [a, b] in nn.init.trunc_normal_. "
#                       "The distribution of values may be incorrect.",
#                       stacklevel=2)

#     with torch.no_grad():
#         # Values are generated by using a truncated uniform distribution and
#         # then using the inverse CDF for the normal distribution.
#         # Get upper and lower cdf values
#         l = norm_cdf((a - mean) / std)
#         u = norm_cdf((b - mean) / std)

#         # Uniformly fill tensor with values from [l, u], then translate to
#         # [2l-1, 2u-1].
#         tensor.uniform_(2 * l - 1, 2 * u - 1)

#         # Use inverse cdf transform for normal distribution to get truncated
#         # standard normal
#         tensor.erfinv_()

#         # Transform to proper mean, std
#         tensor.mul_(std * math.sqrt(2.))
#         tensor.add_(mean)

#         # Clamp to ensure it's in the proper range
#         tensor.clamp_(min=a, max=b)
#         return tensor


def _no_grad_fill_(tensor, val):
    with torch.no_grad():
        return (tensor[0].fill_(val), tensor[1].fill_(val))


def _no_grad_zero_(tensor):
    with torch.no_grad():
        return (tensor[0].zero_(), tensor[1].zero_())

##TODO: implement 
# def calculate_gain(nonlinearity, param=None):
#     r"""Return the recommended gain value for the given nonlinearity function.
#     The values are as follows:

#     ================= ====================================================
#     nonlinearity      gain
#     ================= ====================================================
#     Linear / Identity :math:`1`
#     Conv{1,2,3}D      :math:`1`
#     Sigmoid           :math:`1`
#     Tanh              :math:`\frac{5}{3}`
#     ReLU              :math:`\sqrt{2}`
#     Leaky Relu        :math:`\sqrt{\frac{2}{1 + \text{negative\_slope}^2}}`
#     ================= ====================================================

#     Args:
#         nonlinearity: the non-linear function (`nn.functional` name)
#         param: optional parameter for the non-linear function

#     Examples:
#         >>> gain = nn.init.calculate_gain('leaky_relu', 0.2)  # leaky_relu with negative_slope=0.2
#     """
#     linear_fns = ['linear', 'conv1d', 'conv2d', 'conv3d', 'conv_transpose1d', 'conv_transpose2d', 'conv_transpose3d']
#     if nonlinearity in linear_fns or nonlinearity == 'sigmoid':
#         return 1
#     elif nonlinearity == 'tanh':
#         return 5.0 / 3
#     elif nonlinearity == 'relu':
#         return math.sqrt(2.0)
#     elif nonlinearity == 'leaky_relu':
#         if param is None:
#             negative_slope = 0.01
#         elif not isinstance(param, bool) and isinstance(param, int) or isinstance(param, float):
#             # True/False are instances of int, hence check above
#             negative_slope = param
#         else:
#             raise ValueError("negative_slope {} not a valid number".format(param))
#         return math.sqrt(2.0 / (1 + negative_slope ** 2))
#     else:
#         raise ValueError("Unsupported nonlinearity {}".format(nonlinearity))


def uniform_(tensor, a=0., b=1.):
    # type: (Tensor, float, float) -> Tensor
    r"""Fills the input Tensor with values drawn from the uniform
    distribution :math:`\mathcal{U}(a, b)`.

    Args:
        tensor: an n-dimensional `torch.Tensor`
        a: the lower bound of the uniform distribution
        b: the upper bound of the uniform distribution

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.uniform_(w)
    """
    tensor = _tensorprocessor._preprocess(tensor)
    return _tensorprocessor._postprocess(_no_grad_uniform_(tensor, a, b))


def normal_(tensor, mean=0., std=1.):
    # type: (Tensor, float, float) -> Tensor
    r"""Fills the input Tensor with values drawn from the normal
    distribution :math:`\mathcal{N}(\text{mean}, \text{std}^2)`.

    Args:
        tensor: an n-dimensional `torch.Tensor`
        mean: the mean of the normal distribution
        std: the standard deviation of the normal distribution

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.normal_(w)
    """
    tensor = _tensorprocessor._preprocess(tensor)
    return _tensorprocessor._postprocess(_no_grad_normal_(tensor, mean, std))

# def trunc_normal_(tensor, mean=0., std=1., a=-2., b=2.):
#     # type: (Tensor, float, float, float, float) -> Tensor
#     r"""Fills the input Tensor with values drawn from a truncated
#     normal distribution. The values are effectively drawn from the
#     normal distribution :math:`\mathcal{N}(\text{mean}, \text{std}^2)`
#     with values outside :math:`[a, b]` redrawn until they are within
#     the bounds. The method used for generating the random values works
#     best when :math:`a \leq \text{mean} \leq b`.

#     Args:
#         tensor: an n-dimensional `torch.Tensor`
#         mean: the mean of the normal distribution
#         std: the standard deviation of the normal distribution
#         a: the minimum cutoff value
#         b: the maximum cutoff value

#     Examples:
#         >>> w = torch.empty(3, 5)
#         >>> nn.init.trunc_normal_(w)
#     """
#     return _no_grad_trunc_normal_(tensor, mean, std, a, b)


def constant_(tensor, val):
    # type: (Tensor, float) -> Tensor
    r"""Fills the input Tensor with the value :math:`\text{val}`.

    Args:
        tensor: an n-dimensional `torch.Tensor`
        val: the value to fill the tensor with

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.constant_(w, 0.3)
    """
    tensor = _tensorprocessor._preprocess(tensor)
    return _tensorprocessor._postprocess(_no_grad_fill_(tensor, val))

def ones_(tensor):
    # type: (Tensor) -> Tensor
    r"""Fills the input Tensor with the scalar value `1`.

    Args:
        tensor: an n-dimensional `torch.Tensor`

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.ones_(w)
    """
    tensor = _tensorprocessor._preprocess(tensor)
    return _tensorprocessor._postprocess(_no_grad_fill_(tensor, 1.))

def zeros_(tensor):
    # type: (Tensor) -> Tensor
    r"""Fills the input Tensor with the scalar value `0`.

    Args:
        tensor: an n-dimensional `torch.Tensor`

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.zeros_(w)
    """
    tensor = _tensorprocessor._preprocess(tensor)
    return _tensorprocessor._postprocess(_no_grad_zero_(tensor))

def eye_(tensor):
    r"""Fills the 2-dimensional input `Tensor` with the identity
    matrix. Preserves the identity of the inputs in `Linear` layers, where as
    many inputs are preserved as possible.

    Args:
        tensor: a 2-dimensional `torch.Tensor`

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.eye_(w)
    """
    tensor = _tensorprocessor._preprocess(tensor)
    torch.nn.init.eye_(tensor[0])
    torch.nn.init.eye_(tensor[1])
    return _tensorprocessor._postprocess(tensor)

def dirac_(tensor, groups=1):
    r"""Fills the {3, 4, 5}-dimensional input `Tensor` with the Dirac
    delta function. Preserves the identity of the inputs in `Convolutional`
    layers, where as many input channels are preserved as possible. In case
    of groups>1, each group of channels preserves identity

    Args:
        tensor: a {3, 4, 5}-dimensional `torch.Tensor`
        groups (optional): number of groups in the conv layer (default: 1)
    Examples:
        >>> w = torch.empty(3, 16, 5, 5)
        >>> nn.init.dirac_(w)
        >>> w = torch.empty(3, 24, 5, 5)
        >>> nn.init.dirac_(w, 3)
    """
    tensor = _tensorprocessor._preprocess(tensor)
    torch.nn.init.dirac_(tensor[0], groups=groups)
    torch.nn.init.dirac_(tensor[1], groups=groups)
    return _tensorprocessor._postprocess(tensor)

def _calculate_fan_in_and_fan_out(tensor):
    dimensions = tensor.dim()
    if dimensions < 2:
        raise ValueError("Fan in and fan out can not be computed for tensor with fewer than 2 dimensions")

    num_input_fmaps = tensor.size(1)
    num_output_fmaps = tensor.size(0)
    receptive_field_size = tensor[0][0].numel() if tensor.dim() > 2 else 1
    fan_in = num_input_fmaps * receptive_field_size
    fan_out = num_output_fmaps * receptive_field_size

    return fan_in, fan_out

def xavier_uniform_(tensor, gain=1.):
    # type: (Tensor, float) -> Tensor
    r"""Fills the input `Tensor` with values according to the method
    described in `Understanding the difficulty of training deep feedforward
    neural networks` - Glorot, X. & Bengio, Y. (2010), using a uniform
    distribution. The resulting tensor will have values sampled from
    :math:`\mathcal{U}(-a, a)` where

    .. math::
        a = \text{gain} \times \sqrt{\frac{6}{\text{fan\_in} + \text{fan\_out}}}

    Also known as Glorot initialization.

    Args:
        tensor: an n-dimensional `torch.Tensor`
        gain: an optional scaling factor

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.xavier_uniform_(w, gain=nn.init.calculate_gain('relu'))
    """
    tensor = _tensorprocessor._preprocess(tensor)
    torch.nn.init.xavier_uniform_(tensor[0], gain=gain/math.sqrt(2))
    torch.nn.init.xavier_uniform_(tensor[1], gain=gain/math.sqrt(2))
    return _tensorprocessor._postprocess(tensor)

def xavier_normal_(tensor, gain=1.):
    # type: (Tensor, float) -> Tensor
    r"""Fills the input `Tensor` with values according to the method
    described in `Understanding the difficulty of training deep feedforward
    neural networks` - Glorot, X. & Bengio, Y. (2010), using a normal
    distribution. The resulting tensor will have values sampled from
    :math:`\mathcal{N}(0, \text{std}^2)` where

    .. math::
        \text{std} = \text{gain} \times \sqrt{\frac{2}{\text{fan\_in} + \text{fan\_out}}}

    Also known as Glorot initialization.

    Args:
        tensor: an n-dimensional `torch.Tensor`
        gain: an optional scaling factor

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.xavier_normal_(w)
    """
    tensor = _tensorprocessor._preprocess(tensor)
    torch.nn.init.xavier_normal_(tensor[0], gain=gain/math.sqrt(2))
    torch.nn.init.xavier_normal_(tensor[1], gain=gain/math.sqrt(2))
    return _tensorprocessor._postprocess(tensor)

def _calculate_correct_fan(tensor, mode):
    mode = mode.lower()
    valid_modes = ['fan_in', 'fan_out']
    if mode not in valid_modes:
        raise ValueError(f"Mode {mode} not supported, please use one of {valid_modes}")

    fan_in, fan_out = _calculate_fan_in_and_fan_out(tensor)
    return fan_in if mode == 'fan_in' else fan_out

def kaiming_uniform_(tensor, a=0.0, mode='fan_in', nonlinearity='leaky_relu'):
    r"""Fills the input `Tensor` with values according to the method
    described in `Delving deep into rectifiers: Surpassing human-level
    performance on ImageNet classification` - He, K. et al. (2015), using a
    uniform distribution. The resulting tensor will have values sampled from
    :math:`\mathcal{U}(-\text{bound}, \text{bound})` where

    .. math::
        \text{bound} = \text{gain} \times \sqrt{\frac{3}{\text{fan\_mode}}}

    Also known as He initialization.

    Args:
        tensor: an n-dimensional `torch.Tensor`
        a: the negative slope of the rectifier used after this layer (only
            used with ``'leaky_relu'``)
        mode: either ``'fan_in'`` (default) or ``'fan_out'``. Choosing ``'fan_in'``
            preserves the magnitude of the variance of the weights in the
            forward pass. Choosing ``'fan_out'`` preserves the magnitudes in the
            backwards pass.
        nonlinearity: the non-linear function (`nn.functional` name),
            recommended to use only with ``'relu'`` or ``'leaky_relu'`` (default).

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.kaiming_uniform_(w, mode='fan_in', nonlinearity='relu')
    """
    a = math.sqrt(1 + 2 * a * a)
    tensor = _tensorprocessor._preprocess(tensor)
    torch.nn.init.kaiming_uniform_(tensor[0], a=a, mode=mode, nonlinearity=nonlinearity)
    torch.nn.init.kaiming_uniform_(tensor[1], a=a, mode=mode, nonlinearity=nonlinearity)
    return _tensorprocessor._postprocess(tensor)

def kaiming_normal_(tensor, a=0, mode='fan_in', nonlinearity='leaky_relu'):
    r"""Fills the input `Tensor` with values according to the method
    described in `Delving deep into rectifiers: Surpassing human-level
    performance on ImageNet classification` - He, K. et al. (2015), using a
    normal distribution. The resulting tensor will have values sampled from
    :math:`\mathcal{N}(0, \text{std}^2)` where

    .. math::
        \text{std} = \frac{\text{gain}}{\sqrt{\text{fan\_mode}}}

    Also known as He initialization.

    Args:
        tensor: an n-dimensional `torch.Tensor`
        a: the negative slope of the rectifier used after this layer (only
            used with ``'leaky_relu'``)
        mode: either ``'fan_in'`` (default) or ``'fan_out'``. Choosing ``'fan_in'``
            preserves the magnitude of the variance of the weights in the
            forward pass. Choosing ``'fan_out'`` preserves the magnitudes in the
            backwards pass.
        nonlinearity: the non-linear function (`nn.functional` name),
            recommended to use only with ``'relu'`` or ``'leaky_relu'`` (default).

    Examples:
        >>> w = torch.empty(3, 5)
        >>> nn.init.kaiming_normal_(w, mode='fan_out', nonlinearity='relu')
    """
    a = math.sqrt(1 + 2 * a * a)
    tensor = _tensorprocessor._preprocess(tensor)
    torch.nn.init.kaiming_normal_(tensor[0], a=a, mode=mode, nonlinearity=nonlinearity)
    torch.nn.init.kaiming_normal_(tensor[1], a=a, mode=mode, nonlinearity=nonlinearity)
    return _tensorprocessor._postprocess(tensor)

# def orthogonal_(tensor, gain=1):
#     r"""Fills the input `Tensor` with a (semi) orthogonal matrix, as
#     described in `Exact solutions to the nonlinear dynamics of learning in deep
#     linear neural networks` - Saxe, A. et al. (2013). The input tensor must have
#     at least 2 dimensions, and for tensors with more than 2 dimensions the
#     trailing dimensions are flattened.

#     Args:
#         tensor: an n-dimensional `torch.Tensor`, where :math:`n \geq 2`
#         gain: optional scaling factor

#     Examples:
#         >>> w = torch.empty(3, 5)
#         >>> nn.init.orthogonal_(w)
#     """
#     if tensor.ndimension() < 2:
#         raise ValueError("Only tensors with 2 or more dimensions are supported")

#     rows = tensor.size(0)
#     cols = tensor.numel() // rows
#     flattened = tensor.new(rows, cols).normal_(0, 1)

#     if rows < cols:
#         flattened.t_()

#     # Compute the qr factorization
#     q, r = torch.qr(flattened)
#     # Make Q uniform according to https://arxiv.org/pdf/math-ph/0609050.pdf
#     d = torch.diag(r, 0)
#     ph = d.sign()
#     q *= ph

#     if rows < cols:
#         q.t_()

#     with torch.no_grad():
#         tensor.view_as(q).copy_(q)
#         tensor.mul_(gain)
#     return tensor

# def sparse_(tensor, sparsity, std=0.01):
#     r"""Fills the 2D input `Tensor` as a sparse matrix, where the
#     non-zero elements will be drawn from the normal distribution
#     :math:`\mathcal{N}(0, 0.01)`, as described in `Deep learning via
#     Hessian-free optimization` - Martens, J. (2010).

#     Args:
#         tensor: an n-dimensional `torch.Tensor`
#         sparsity: The fraction of elements in each column to be set to zero
#         std: the standard deviation of the normal distribution used to generate
#             the non-zero values

#     Examples:
#         >>> w = torch.empty(3, 5)
#         >>> nn.init.sparse_(w, sparsity=0.1)
#     """
#     if tensor.ndimension() != 2:
#         raise ValueError("Only tensors with 2 dimensions are supported")

#     rows, cols = tensor.shape
#     num_zeros = int(math.ceil(sparsity * rows))

#     with torch.no_grad():
#         tensor.normal_(0, std)
#         for col_idx in range(cols):
#             row_indices = torch.randperm(rows)
#             zero_indices = row_indices[:num_zeros]
#             tensor[zero_indices, col_idx] = 0
#     return tensor

def trabelsi_standard_(tensor, kind="glorot"):
    """Standard complex initialization proposed in Trabelsi et al. (2018)."""
    kind = kind.lower()
    assert kind in ("glorot", "xavier", "kaiming", "he")

    tensor = _tensorprocessor._preprocess(tensor)

    fan_in, fan_out = _calculate_fan_in_and_fan_out(tensor[0])
    if kind in ["glorot", "xavier"]:
        scale = 1 / math.sqrt(fan_in + fan_out)
    else:
        scale = 1 / math.sqrt(fan_in)

    # Rayleigh(\sigma / \sqrt2) x uniform[-\pi, +\pi] on p. 7
    rho = np.random.rayleigh(scale, size=tensor[0].shape)
    theta = np.random.uniform(-np.pi, +np.pi, size=tensor[0].shape)

    # eq. (8) on p. 6
    with torch.no_grad():
        tensor[0].copy_(torch.from_numpy(np.cos(theta) * rho))
        tensor[1].copy_(torch.from_numpy(np.sin(theta) * rho))

    return _tensorprocessor._postprocess(tensor)

def trabelsi_independent_(tensor, kind="glorot"):
    """Orthogonal complex initialization proposed in Trabelsi et al. (2018)."""
    kind = kind.lower()
    assert kind in ("glorot", "xavier", "kaiming", "he")

    tensor = _tensorprocessor._preprocess(tensor)

    ndim = tensor[0].dim()
    if ndim == 2:
        shape = tensor[0].shape
    else:
        shape = int(np.prod(tensor[0].shape[:2])), int(np.prod(tensor[0].shape[2:]))

    # generate a semi-unitary (orthogonal) matrix from a random matrix
    # M = U V is semi-unitary: V^H U^H U V = I_k
    Z = np.random.rand(*shape) + 1j * np.random.rand(*shape)

    # Z is n x m, so u is n x n and vh is m x m
    u, _, vh = np.linalg.svd(Z, compute_uv=True, full_matrices=True, hermitian=False)
    k = min(*shape)
    M = np.dot(u[:, :k], vh[:, :k].conjugate().T)

    fan_in, fan_out = _calculate_fan_in_and_fan_out(tensor[0])
    if kind in ["glorot", "xavier"]:
        scale = 1 / math.sqrt(fan_in + fan_out)
    else:
        scale = 1 / math.sqrt(fan_in)

    M /= M.std() / scale
    M = M.reshape(tensor[0].shape)

    with torch.no_grad():
        tensor[0].copy_(torch.from_numpy(M.real))
        tensor[1].copy_(torch.from_numpy(M.imag))

    return _tensorprocessor._postprocess(tensor)