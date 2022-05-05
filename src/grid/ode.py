# GRID is a numerical integration module for quantum chemistry.
#
# Copyright (C) 2011-2019 The GRID Development Team
#
# This file is part of GRID.
#
# GRID is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# GRID is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
# --
"""Generic ode solver module."""

from numbers import Number
from typing import Union

from grid.rtransform import BaseTransform

import numpy as np

from scipy.integrate import solve_bvp

from sympy import bell


class ODE:
    r"""
    Linear ordinary differential equation solver with boundary conditions.

    Solves a linear ordinary differential equation of order :math:`K` of the form

    .. math::
        \sum_{k=0}^{K} a_k(x) \frac{d^k y(x)}{dx^k} = f(x)

    with boundary conditions on the two end-points for some unknown function
    :math:`y(x)` with independent variable :math:`x`. Currently only supports :math:`K`-th
    order less than or equal to three.

    It also supports the ability to transform the independent variable :math:`x`
    to another domain :math:`g(x)` for some :math:`K`-th differentiable transformation
    :math:`g(x)`.  This is particularly useful to convert infinite domains, e.g.
    :math:`[0, \infty)`, to a finite interval.

    """

    @staticmethod
    def solve_ode(
        x: np.ndarray,
        fx: callable,
        coeffs: Union[list, np.ndarray],
        bd_cond: list,
        transform: BaseTransform = None,
        tol: float = 1e-4,
        max_nodes: int = 5000,
        initial_guess_y: np.ndarray = None,
    ):
        r"""Solve a linear ODE with boundary conditions.

        Parameters
        ----------
        x : np.ndarray(N,)
            Points of the independent variable/domain.
        fx : callable
            Right-hand function :math:`f(x)`.
        coeffs : list[callable or float] or ndarray(K + 1,)
            Coefficients :math:`a_k` of each term :math:`\frac{d^k y(x)}{d x^k}`
            ordered from 0 to K. Either a list of callable functions :math:`a_k(x)` that depends
            on :math:`x` or array of constants :math:`\{a_k\}_{k=0}^{K}`.
        bd_cond : list[list[int, int, float]]
            Boundary condition specified by list of three entries [i, j, C], where
            :math:`i \in \{0, 1\}` determines whether the lower or upper bound is being
            constrained, :math:`j \in \{0, \cdots, K\}` determines which derivative
            :math:`\frac{d^j y}{dx^j}` is being constrained, and :math:`C`
            determines the boundary constraint value, i.e. :math:`\frac{d^j y}{dx^j} = C`.
            If `transform` is given, then the constraint of the derivatives is assumed
            to be with respect to the new coordinate i.e. :math:`\frac{d^j y}{dr^j} = C`.
        transform : BaseTransform, optional
            Transformation from one domain :math:`x` to another :math:`r := g(x)`.
        tol : float, optional
            Tolerance of the ODE solver and for the boundary condition residuals.
            See `scipy.integrate.solve_bvp` for more info.
        max_nodes : int, optional
            The maximum number of mesh nodes that determine termination.
            See `scipy.integrate.solve_bvp` function for more info.
        initial_guess_y : ndarray, optional
            Initial guess for :math:`y(x)` at the points `x`. If not provided, then
            random set of points from 0 to 1 is used.

        Returns
        -------
        PPoly
            scipy.interpolate.PPoly instance for interpolating new values
            and its derivative

        """
        order = len(coeffs) - 1
        if len(bd_cond) != order:
            raise NotImplementedError(
                "# of boundary condition need to be the same as ODE order."
                f"Expect: {order}, got: {len(bd_cond)}."
            )
        if order > 3:
            raise NotImplementedError("Only support 3rd order ODE or less.")

        # define 1st order ODE for solver
        def func(x, y):
            if transform:
                dy_dx = ODE._rearrange_trans_ode(x, y, coeffs, transform, fx)
            else:
                coeffs_mt = ODE._construct_coeff_array(x, coeffs)
                dy_dx = ODE._rearrange_ode(x, y, coeffs_mt, fx(x))
            return np.vstack((*y[1:], dy_dx))

        # define boundary condition
        def bc(ya, yb):
            bonds = [ya, yb]
            conds = []
            for i, deriv, value in bd_cond:
                conds.append(bonds[i][deriv] - value)
            return np.array(conds)

        y = np.random.rand(order, x.size)
        res = solve_bvp(func, bc, x, y, tol=1e-4)
        # raise error if didn't converge
        if res.status != 0:
            raise ValueError(
                f"The ode solver didn't converge, got status: {res.status}"
            )
        return res.sol

    @staticmethod
    def _transform_ode_from_derivs(
        coeffs: Union[list, np.ndarray], deriv_transformation: list, r: np.ndarray
    ):
        r"""
        Transform the coefficients of ODE from one variable to another evaluated on mesh points.

        Given a :math:`K`-th differentiable transformation function :math:`g(r)`
        and a linear ODE of :math:`K`-th order on independent variable :math:`r`

        .. math::
            \sum_{k=1}^{K} a_k(r) \frac{d^k y}{d r^k}.

        This transforms it into a new coordinate system :math:`g(r) =: x`

        .. math::
            \sum_{j=1}^K b_j(x) \frac{d^j y}{d x^j},

        where :math:`b_j(x) = \sum_{k=1}^K a_k(x) B_{k, j}(g(r), g^\prime(r), \cdots,
        g^{k - j + 1}(r))`.

        Parameters
        ----------
        coeffs : list[callable or number] or ndarray
            Coefficients :math:`a_k` of each term :math:`\frac{d^k y(x)}{d r^k}`
            ordered from 0 to K. Either a list of callable functions :math:`a_k(r)` that depends
            on :math:`r` or array of constants :math:`\{a_k\}_{k=0}^{K}`.
        deriv_transformation : list[callable]
            List of functions for compute transformation derivatives from 1 to :math:`K`.
        r : ndarray
            Points from the original domain that is to be transformed.

        Returns
        -------
        ndarray((K+1, N))
            Coefficients :math:`b_j(x)` of the new ODE with respect to variable :math:`x`.

        """
        derivs = np.array([dev(r) for dev in deriv_func_list])
        total = len(coeff_a)
        # coeff_a = np.zeros((total, r.size), dtype=float)
        # # construct coeff matrix
        # for i, val in enumerate(coeff_a_ori):
        #     if isinstance(val, Number):
        #         coeff_a[i] += val
        #     else:
        #         coeff_a[i] += val(r)
        coeff_a_mtr = ODE._construct_coeff_array(r, coeff_a)
        coeff_b = np.zeros((total, r.size), dtype=float)
        # constrcut 1 - 3 directly
        coeff_b[0] += coeff_a_mtr[0]
        if total > 1:
            coeff_b[1] += coeff_a_mtr[1] * derivs[0]
        if total > 2:
            coeff_b[1] += coeff_a_mtr[2] * derivs[1]
            coeff_b[2] += coeff_a_mtr[2] * derivs[0] ** 2
        if total > 3:
            coeff_b[1] += coeff_a_mtr[3] * derivs[2]
            coeff_b[2] += coeff_a_mtr[3] * 3 * derivs[0] * derivs[1]
            coeff_b[3] += coeff_a_mtr[3] * derivs[0] ** 3

        # construct 4th order and onwards
        # if total >= 4:
        #     for i, j in enumerate(r):
        #         for coeff_index in range(4, total):
        #             for dev_order in range(coeff_index, total):  # efficiency
        #                 coeff_b[coeff_index, i] += (
        #                     float(bell(dev_order, coeff_index, derivs[:, i]))
        #                     * coeff_a[dev_order]
        #                 )
        return coeff_b

    @staticmethod
    def _transform_ode_from_rtransform(
        coeff_a: Union[list, np.ndarray], tf: BaseTransform, x: np.ndarray
    ):
        r"""
        Transform the coefficients of ODE from one variable to another based on Transform object.

        Given a :math:`K`-th differentiable transformation function :math:`g(r)`
        and a linear ODE of :math:`K`-th order

        .. math::
            \sum_{k=1}^{K} a_k(r) \frac{d^k y}{d r^k}.

        This transforms it into a new coordinate system with variable :math:`g(r) =: x` via

        .. math::
            \sum_{j=1}^K b_j(x) \frac{d^j y}{d x^j},

        where :math:`b_j(x) = \sum_{k=1}^K a_k(x) B_{k, j}(g(r), g^\prime(r), \cdots,
        g^{k - j + 1}(r))`.

        Parameters
        ----------
        coeff_a : list[number or callable] or np.ndarray
            Coefficients for normal ODE
        tf : BaseTransform
            Transform instance of :math:`g(x)`
        x : np.ndarray(N,)
            Points of the independent variable/domain.

        Returns
        -------
        ndarray((K+1, N))
            Coefficients :math:`b_j(x)` of the new ODE with respect to variable :math:`x`.

        """
        deriv_func = [tf.deriv, tf.deriv2, tf.deriv3]
        r = tf.inverse(x)
        return ODE._transform_ode_from_derivs(coeff_a, deriv_func, r)

    @staticmethod
    def _transform_and_rearrange_to_explicit_ode(
        x: np.ndarray,
        y: np.ndarray,
        coeff_a: Union[list, np.ndarray],
        tf: BaseTransform,
        fx_func: callable,
    ):
        r"""Rearrange coefficients in transformed domain.

        Parameters
        ----------
        x : np.ndarray(N,)
            Points of the independent variable/domain.
        y : np.ndarray(K + 1, N)
            Initial guess for the function values and its derivatives
        coeff_a : list[number or callable] or np.ndarray(K + 1)
            Coefficients :math:`a_k` of each term :math:`\frac{d^k y(x)}{d x^k}`
            ordered from 0 to K.  Each coefficient can either be a callable function
            :math:`a_k(x)` or a constant number :math:`a_k`.
        tf: BaseTransform
            Transform instance of :math:`g(x)`.
        fx_func : Callable
            Right-hand function of the ODE.

        Returns
        -------
        np.ndarray(N,)
            Expression for the right side of the ODE equation after converting it
            to explicit form evaluated on all N points.

        """
        coeff_b = ODE._transformed_coeff_ode(coeff_a, tf, x)
        result = ODE._rearrange_ode(x, y, coeff_b, fx_func(tf.inverse(x)))
        return result

    @staticmethod
    def _construct_coeff_array(x, coeff):
        """Construct coefficient matrix for given points.

        Parameters
        ----------
        x : np.ndarray(K,)
            Points on the mesh grid
        coeff : list[number or callable] or np.ndarray, length N
            Coefficient for each derivatives in the ode

        Returns
        -------
        np.ndarray(N, K)
            Numerical coefficient value for ODE
        """
        coeff_mtr = np.zeros((len(coeff), x.size), dtype=float)
        for i, val in enumerate(coeff):
            if isinstance(val, Number):
                coeff_mtr[i] += val
            else:
                coeff_mtr[i] += val(x)
        return coeff_mtr

    @staticmethod
    def _rearrange_to_explicit_ode(y: np.ndarray, coeff_b: np.ndarray, fx: np.ndarray):
        r"""Rearrange ODE into explicit form for conversion to first-order ODE (SciPy solver).

        Returns array with :math:`n`-th entry

        .. math::
            \frac{f(x_n) -\sum_{k=0}^{K - 1} a_k(x_n) \frac{d^k y(x_n)}{d x^k}}{a_{K}(x_n)},

        of the :math:`n`-th point :math:`x` such that :math:`a_K \neq 0`.
        This arises from re-arranging the ODE of :math:`K`-th order into explicit form.

        Parameters
        ----------
        y : np.ndarray(K + 1, N)
            Initial guess for the function values and its :math:`k`-th order derivatives
            from 1 to :math:`K`, evaluated on the :math:`n`-th point :math:`x_n`.
        coeff_b : ndarray(K + 1, N)
            Coefficients :math:`a_k(x_n)` of each term :math:`\frac{d^k y(x)}{d x^k}`
            ordered from 0 to K evaluated on the :math:`n`-th point :math:`x_n`.
        fx : np.ndarray(N,)
            Right hand-side of the ODE equation, function :math:`f(x_n)` evaluated on the
            :math:`n`-th point :math:`x_n`.

        Returns
        -------
        np.ndarray(N,)
            Expression for the right side of the ODE equation after converting it
            to explicit form evaluated on N-th points.

        """
        result = fx
        # Go through all rows except the last-element.
        for i, b in enumerate(coeff_b[:-1]):
            # array of size N: a_k(x_n) * (d^k y(x_n) / d x^k)
            result -= b * y[i]
        return result / coeff_b[-1]
