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
r"""Cubic Grid Testing."""

from unittest import TestCase

from grid.cubic import Tensor1DGrids, UniformCubicGrid, _HyperRectangleGrid
from grid.onedgrid import GaussLaguerre, MidPoint

import numpy as np
from numpy.testing import assert_allclose


class TestHyperRectangleGrid(TestCase):
    r"""Test HyperRectangleGrid class."""

    def test_get_points_along_axes(self):
        r"""Test getting the points alongside each axis."""
        # Three Dimensions
        points = np.array(
            [
                [0, 0, 0],
                [0, 0, 1],
                [0, 1, 0],
                [0, 1, 1],
                [1, 0, 0],
                [1, 0, 1],
                [1, 1, 0],
                [1, 1, 1],
            ]
        )
        weights = np.array([1.0] * points.shape[0])
        grid = _HyperRectangleGrid(points, weights, (2, 2, 2))
        x, y, z = grid.get_points_along_axes()
        assert_allclose(x, np.array([0, 1]))
        assert_allclose(y, np.array([0, 1]))
        assert_allclose(z, np.array([0, 1]))

        # Two Dimensions
        points = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        weights = np.array([1.0] * points.shape[0])
        grid = _HyperRectangleGrid(points, weights, (2, 2))
        x, y = grid.get_points_along_axes()
        assert_allclose(x, np.array([0, 1]))
        assert_allclose(y, np.array([0, 1]))

    def test_raises_error_when_constructing_grid(self):
        r"""Test parameters of constructing a hyper-rectangular grid."""
        points = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        weights = np.array([1.0] * points.shape[0])
        # Test with shape length greater than 3
        with self.assertRaises(ValueError) as err:
            _HyperRectangleGrid(points, weights, (2, 2, 2, 2))
        self.assertEqual(
            "Argument shape should have length two or three; got length 4.",
            str(err.exception),
        )
        # Test with shape with number of points is one.
        with self.assertRaises(ValueError) as err:
            _HyperRectangleGrid(points, weights, (2, 2, 1))
        self.assertEqual(
            "Argument shape should be greater than one in all directions (2, 2, 1).",
            str(err.exception),
        )
        # Test the product of shape doesn't equal the number of points
        with self.assertRaises(ValueError) as err:
            _HyperRectangleGrid(points, weights, (2, 3))
        self.assertEqual(
            "The product of every element in shape 6 should match the number of points 4.",
            str(err.exception),
        )
        # Test the dimension specified by shape doesn't match the number of points.
        points = np.array([[0, 0, 0], [0, 1, 0], [1, 0, 1], [1, 1, 1]])
        with self.assertRaises(ValueError) as err:
            _HyperRectangleGrid(points, weights, (2, 2))
        self.assertEqual(
            "The dimension of the shape/grid 2 should match the dimension of the points 3.",
            str(err.exception),
        )


class TestTensor1DGrids(TestCase):
    r"""Test Tensor Product of 1D Grids."""

    def test_point_and_weights_are_correct(self):
        r"""Test that the points and weights are correctly computed."""
        oned = GaussLaguerre(10)
        cubic = Tensor1DGrids(oned, oned, oned)

        index = 0  # Index for cubic points.
        for i in range(oned.size):
            for j in range(oned.size):
                for k in range(oned.size):
                    actual_pt = np.array(
                        [oned.points[i], oned.points[j], oned.points[k]]
                    )
                    assert_allclose(actual_pt, cubic.points[index, :])
                    actual_weight = oned.weights[i] * oned.weights[j] * oned.weights[k]
                    assert_allclose(actual_weight, cubic.weights[index])
                    index += 1

    def test_interpolation_of_gaussian_vertorized(self):
        r"""Test interpolation of a Gaussian function with vectorization."""
        oned = MidPoint(50)
        cubic = Tensor1DGrids(oned, oned, oned)

        def gaussian(points):
            return np.exp(-3 * np.linalg.norm(points, axis=1) ** 2.0)

        gaussian_pts = gaussian(cubic.points)
        num_pts = 500
        random_pts = np.random.uniform(-0.9, 0.9, (num_pts, 3))
        interpolated = cubic.interpolate_function(
            random_pts, gaussian_pts, use_log=False
        )
        assert_allclose(interpolated, gaussian(random_pts), rtol=1e-5, atol=1e-6)

    def test_interpolation_of_linear_function_using_scipy_linear_method(self):
        r"""Test interpolation of a linear function using scipy with linear method."""
        oned = MidPoint(50)
        cubic = Tensor1DGrids(oned, oned, oned)

        def linear_func(points):
            return np.dot(np.array([1.0, 2.0, 3.0]), points.T)

        gaussian_pts = linear_func(cubic.points)
        num_pts = 50
        random_pts = np.random.uniform(-0.9, 0.9, (num_pts, 3))
        interpolated = cubic.interpolate_function(
            random_pts, gaussian_pts, use_log=False, method="linear"
        )
        assert_allclose(interpolated, linear_func(random_pts))

    def test_interpolation_of_constant_function_using_scipy_nearest_method(self):
        r"""Test interpolation of a constant function using scipy with nearest method."""
        oned = MidPoint(50)
        cubic = Tensor1DGrids(oned, oned, oned)

        def linear_func(points):
            return (
                np.array([1.0] * points.shape[0])
                + np.random.random((points.shape[0])) * 1.0e-6
            )

        gaussian_pts = linear_func(cubic.points)
        num_pts = 5
        random_pts = np.random.uniform(-0.9, 0.9, (num_pts, 3))
        for pt in random_pts:
            interpolated = cubic.interpolate_function(
                pt, gaussian_pts, use_log=False, method="nearest"
            )
            assert_allclose(interpolated, linear_func(np.array([pt]))[0], rtol=1e-6)

    def test_interpolation_of_various_derivative_polynomial(self):
        r"""Test interpolation of the derivative of a quadraticpolynomial function."""
        oned = MidPoint(200)
        cubic = Tensor1DGrids(oned, oned, oned)

        def quadratic_polynomial(points):
            return np.sum(points ** 4, axis=1)

        def derivative_wrt_one_var(point, i_var_deriv):
            if i_var_deriv == 0:
                return 4 * point[0, 0] ** 3
            if i_var_deriv == 1:
                return 4 * point[0, 1] ** 3
            if i_var_deriv == 2:
                return 4 * point[0, 2] ** 3

        def derivative_second_x(point):
            return 4 * 3 * point[0, 0] ** 2

        # Evaluate function over the grid
        gaussian_pts = quadratic_polynomial(cubic.points)
        pt = np.random.uniform(-1, 1, (1, 3))
        # Test taking derivative in x-direction
        interpolated = cubic.interpolate_function(
            pt, gaussian_pts, use_log=False, nu_x=1
        )
        assert_allclose(
            interpolated, derivative_wrt_one_var(pt, 0), rtol=1e-4, atol=1e-4
        )

        # Test taking derivative in y-direction
        interpolated = cubic.interpolate_function(
            pt, gaussian_pts, use_log=False, nu_y=1
        )
        assert_allclose(
            interpolated, derivative_wrt_one_var(pt, 1), rtol=1e-4, atol=1e-4
        )

        # Test taking derivative in z-direction
        interpolated = cubic.interpolate_function(
            pt, gaussian_pts, use_log=False, nu_z=1
        )
        assert_allclose(
            interpolated, derivative_wrt_one_var(pt, 2), rtol=1e-4, atol=1e-4
        )

        # Test taking derivative in x,y,z-direction
        interpolated = cubic.interpolate_function(
            pt, gaussian_pts, use_log=False, nu_x=1, nu_y=1, nu_z=1
        )
        assert np.abs(interpolated) < 1e-8

        # Test taking second-derivative in x-direction
        interpolated = cubic.interpolate_function(
            pt, gaussian_pts, use_log=False, nu_x=2, nu_y=0, nu_z=0
        )
        assert_allclose(interpolated, derivative_second_x(pt), rtol=1e-3)

    def test_interpolation_of_various_derivative_gaussian_using_logarithm(self):
        r"""Test interpolation of the derivatives of a Gaussian function."""
        oned = MidPoint(150)
        cubic = Tensor1DGrids(oned, oned, oned)

        def gaussian(points):
            return np.exp(-3 * np.linalg.norm(points, axis=1) ** 2.0)

        def derivative_wrt_one_var(point, i_var_deriv):
            return (
                np.exp(-3 * np.linalg.norm(point) ** 2.0)
                * point[i_var_deriv]
                * (-3 * 2.0)
            )

        def derivative_second_x(point):
            return np.exp(-3 * np.linalg.norm(point) ** 2.0) * point[0] ** 2.0 * (
                -3 * 2.0
            ) ** 2.0 + np.exp(-3 * np.linalg.norm(point) ** 2.0) * (-3 * 2.0)

        gaussian_pts = gaussian(cubic.points)

        pt = np.random.uniform(-0.5, 0.5, (3,))
        # Test taking derivative in x-direction
        interpolated = cubic.interpolate_function(
            pt[np.newaxis, :], gaussian_pts, use_log=True, nu_x=1
        )
        assert_allclose(interpolated, derivative_wrt_one_var(pt, 0), rtol=1e-4)

        # Test taking derivative in z-direction
        interpolated = cubic.interpolate_function(
            pt[np.newaxis, :], gaussian_pts, use_log=True, nu_z=1
        )
        assert_allclose(interpolated, derivative_wrt_one_var(pt, 2), rtol=1e-4)

        # Test taking second-derivative in x-direction
        interpolated = cubic.interpolate_function(
            pt[np.newaxis, :], gaussian_pts, use_log=True, nu_x=2, nu_y=0, nu_z=0
        )
        assert_allclose(interpolated, derivative_second_x(pt), rtol=1e-4)

        # Test raises error
        with self.assertRaises(NotImplementedError):
            cubic.interpolate_function(
                pt[np.newaxis, :], gaussian_pts, use_log=True, nu_x=2, nu_y=2
            )

    def test_integration_of_gaussian(self):
        r"""Test integration of a rapidly-decreasing Gaussian."""
        oned = MidPoint(250)
        cubic = Tensor1DGrids(oned, oned, oned)

        def gaussian(points):
            return np.exp(-6 * np.linalg.norm(points, axis=1) ** 2.0)

        gaussian_pts = gaussian(cubic.points)
        desired = np.sqrt(np.pi / 6) ** 3
        actual = cubic.integrate(gaussian_pts)
        assert_allclose(desired, actual, atol=1e-3)

    def test_moving_coordinates_to_index_and_back_three_dimensions(self):
        r"""Test moving from coordinates and index and back in three_dimensions."""
        oned = MidPoint(3)
        cubic = Tensor1DGrids(oned, oned, oned)

        # Convert index to coordinate.
        index = 3
        coord = (0, 1, 0)
        assert_allclose(coord, cubic.index_to_coordinates(index))

        # Convert coordinate to index
        coord = (1, 0, 1)
        index = 10
        assert_allclose(index, cubic.coordinates_to_index(coord))

        # Convert back
        index = 9
        assert_allclose(
            index, cubic.coordinates_to_index(cubic.index_to_coordinates(index))
        )

    def test_moving_coordinates_to_index_and_back_two_dimensions(self):
        r"""Test moving from coordinates and index and back in two dimensions."""
        oned = MidPoint(3)
        cubic = Tensor1DGrids(oned, oned)

        # Convert index to coordinate.
        index = 3
        coord = (1, 0)
        assert_allclose(coord, cubic.index_to_coordinates(index))

        # Convert coordinate to index
        coord = (1, 1)
        index = 4
        assert_allclose(index, cubic.coordinates_to_index(coord))

        # Convert back
        index = 1
        assert_allclose(
            index, cubic.coordinates_to_index(cubic.index_to_coordinates(index))
        )


class TestUniformCubicGrid(TestCase):
    r"""Test Uniform Cubic Grid Class."""

    def test_volume_generalizes_volume_of_cube_with_orthogonal_axes(self):
        r"""Test volume of a cube is the same as multiplying by length of axes."""
        origin = np.array([0.0, 0.0, 0.0])
        axes = np.eye(3)
        shape = np.array([5, 6, 7], dtype=np.int)
        uniform = UniformCubicGrid(origin, axes, shape=shape)
        volume = 5 * 6 * 7
        assert_allclose(volume, uniform._calculate_volume(shape))

    def test_fourier1_weights_are_correct(self):
        r"""Test Fourier1 weights are correct against brute force."""
        origin = np.array([0.0, 0.0, 0.0])
        axes = np.eye(3)
        shape = np.array([5, 6, 7], dtype=np.int)
        volume = (
            5 * 6 * 7
        )  # Volume of cube centered at zero, moves in one step at a time (axes)
        uniform = UniformCubicGrid(origin, axes, shape=shape, weight_type="Fourier1")

        index = 0  # Index to iterate through uniform.weights.
        for j in range(1, shape[0] + 1):
            grid_x = np.arange(1, shape[0] + 1)
            desired_x = np.sum(
                np.sin(j * np.pi * grid_x / (shape[0] + 1))
                * (1 - np.cos(grid_x * np.pi))
                / (grid_x * np.pi)
            )
            for k in range(1, shape[1] + 1):

                grid_y = np.arange(1, shape[1] + 1)
                desired_y = np.sum(
                    np.sin(k * np.pi * grid_y / (shape[1] + 1))
                    * (1 - np.cos(grid_y * np.pi))
                    / (grid_y * np.pi)
                )
                for m in range(1, shape[2] + 1):
                    grid_z = np.arange(1, shape[2] + 1)
                    desired_z = np.sum(
                        np.sin(m * np.pi * grid_z / (shape[2] + 1))
                        * (1 - np.cos(grid_z * np.pi))
                        / (grid_z * np.pi)
                    )
                    desired = (
                        8 * desired_x * desired_y * desired_z * volume / (6 * 7 * 8)
                    )
                    assert_allclose(uniform.weights[index], desired)
                    index += 1

    def test_fourier2_weights_are_correct(self):
        r"""Test that the Fourier2 weights are correct against brute force."""
        origin = np.array([0.0, 0.0, 0.0])
        axes = np.eye(3)
        shape = np.array([5, 6, 7], dtype=np.int)
        volume = (
            5 * 6 * 7
        )  # Volume of cube centered at zero, moves in one step at a time (axes)
        volume *= (
            (4.0 / 5.0) * (5.0 / 6) * (6.0 / 7)
        )  # Alternative volume is used here.
        uniform = UniformCubicGrid(origin, axes, shape=shape, weight_type="Fourier2")
        index = 0  # Index to iterate through uniform.weights.
        for j in range(1, shape[0] + 1):
            # Calculate weight in the x-direction
            grid_x = np.arange(1, shape[0])
            desired_x = (
                2.0 * np.sin((j - 0.5) * np.pi) * np.sin(shape[0] * np.pi / 2) ** 2.0
            )
            desired_x /= shape[0] ** 2.0 * np.pi
            desired_x += (
                4.0
                * np.sum(
                    np.sin((2.0 * j - 1.0) * grid_x * np.pi / shape[0])
                    * np.sin(grid_x * np.pi / 2) ** 2.0
                    / grid_x
                )
                / (shape[0] * np.pi)
            )
            for k in range(1, shape[1] + 1):
                # Calculate weight in the y-direction
                grid_y = np.arange(1, shape[1])
                desired_y = (
                    2.0
                    * np.sin((k - 0.5) * np.pi)
                    * np.sin(shape[1] * np.pi / 2) ** 2.0
                )
                desired_y /= shape[1] ** 2.0 * np.pi
                desired_y += (
                    4.0
                    * np.sum(
                        np.sin((2.0 * k - 1.0) * grid_y * np.pi / shape[1])
                        * np.sin(grid_y * np.pi / 2) ** 2.0
                        / grid_y
                    )
                    / (shape[1] * np.pi)
                )
                for m in range(1, shape[2] + 1):
                    # Calculate weight in the z-direction
                    grid_z = np.arange(1, shape[2])
                    desired_z = (
                        2.0
                        * np.sin((m - 0.5) * np.pi)
                        * np.sin(shape[2] * np.pi / 2) ** 2.0
                    )
                    desired_z /= shape[2] ** 2.0 * np.pi
                    desired_z += (
                        4.0
                        * np.sum(
                            np.sin((2.0 * m - 1.0) * grid_z * np.pi / shape[2])
                            * np.sin(grid_z * np.pi / 2) ** 2.0
                            / grid_z
                        )
                        / (shape[2] * np.pi)
                    )
                    desired = desired_x * desired_y * desired_z * volume
                    assert_allclose(uniform.weights[index], desired)
                    index += 1

    def test_calculating_rectangle_weights_with_orthogonal_axes(self):
        r"""Test calcualting rectangle weights with orthogonal axes."""
        # Set up the grid with easy examples but axes that form a cube.
        origin = np.array([0.0, 0.0, 0.0])
        axes = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        shape = np.array([3, 3, 3], dtype=np.int)
        uniform = UniformCubicGrid(origin, axes, shape, weight_type="Rectangle")
        volume = 3 * 3 * 3  # Volume of cube.
        desired_wghts = np.ones(uniform.size) * volume / np.prod(shape)
        assert_allclose(uniform.weights, desired_wghts)

    def test_calculating_trapezoid_weights_with_orthogonal_axes(self):
        r"""Test calculating trapezoid weights with orthogonal axes."""
        # Set up the grid with easy examples but axes that form a cube.
        origin = np.array([0.0, 0.0, 0.0])
        axes = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        shape = np.array([3, 3, 3], dtype=np.int)
        uniform = UniformCubicGrid(origin, axes, shape, weight_type="Trapezoid")
        volume = 3 * 3 * 3  # Volume of cube.
        desired_wghts = np.ones(uniform.size) * volume / np.prod(shape + 1)
        assert_allclose(uniform.weights, desired_wghts)

    def test_calculating_alternative_weights_with_orthogonal_axes(self):
        r"""Test calcualting alternative weights with orthogonal axes."""
        # Set up the grid with easy examples but axes that form a cube.
        origin = np.array([0.0, 0.0, 0.0])
        axes = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        shape = np.array([3, 3, 3], dtype=np.int)
        uniform = UniformCubicGrid(origin, axes, shape, weight_type="Alternative")
        volume = 3 * 3 * 3  # Volume of cube.
        desired_wghts = (
            np.ones(uniform.size) * volume * np.prod(shape - 1) / np.prod(shape)
        )
        assert_allclose(uniform.weights, desired_wghts)

    def test_integration_with_gaussian(self):
        r"""Test integration against a Gaussian."""
        origin = np.array([-1.0, -1.0, -1.0])
        axes = np.eye(3) * 0.01
        shape = np.array([250, 250, 250], dtype=np.int)

        def gaussian(points):
            return np.exp(-5 * np.linalg.norm(points, axis=1) ** 2.0)

        # Test with rectangle weights.
        uniform = UniformCubicGrid(origin, axes, shape, weight_type="Rectangle")
        gaussian_pts = gaussian(uniform.points)
        desired = np.sqrt(np.pi / 5) ** 3
        actual = uniform.integrate(gaussian_pts)
        assert_allclose(desired, actual, atol=1e-2)

        # Test with Trapezoid weights.
        uniform = UniformCubicGrid(origin, axes, shape, weight_type="Trapezoid")
        gaussian_pts = gaussian(uniform.points)
        desired = np.sqrt(np.pi / 5) ** 3
        actual = uniform.integrate(gaussian_pts)
        assert_allclose(desired, actual, atol=1e-2)

        # Test with Fourier1 weights.
        uniform = UniformCubicGrid(origin, axes, shape, weight_type="Fourier1")
        gaussian_pts = gaussian(uniform.points)
        desired = np.sqrt(np.pi / 5) ** 3
        actual = uniform.integrate(gaussian_pts)
        assert_allclose(desired, actual, atol=1e-2)

    def test_finding_closest_point_to_cubic_grid(self):
        r"""Test finding the closest point to a cubic grid."""
        # Set up the grid with easy examples but axes that form a cube.
        origin = np.array([0.0, 0.0, 0.0])
        axes = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        shape = np.array([3, 3, 3], dtype=np.int)
        uniform = UniformCubicGrid(origin, axes, shape)

        # Create point close to the origin
        pt = np.array([0.1, 0.1, 0.1])
        index = uniform.closest_point(pt, "origin")
        assert index == 0
        index = uniform.closest_point(pt, "closest")
        assert index == 0

        # Create point close to the point with coordinates (1, 1, 1) but whose origin is zero.
        pt = np.array([0.75, 0.75, 0.75])
        index = uniform.closest_point(pt, "origin")
        assert index == 0
        index = uniform.closest_point(pt, "closest")
        assert index == 13

        # Test raises error
        with self.assertRaises(ValueError):
            # Test wrong attribute.
            uniform.closest_point(pt, "not origin or closest")

            # Test axes that are not orthogonal.
            origin = np.array([0.0, 0.0, 0.0])
            axes = np.array([[1.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
            shape = np.array([3, 3, 3], dtype=np.int)
            UniformCubicGrid(origin, axes, shape)

    def test_uniformgrid_points_h2o(self):
        r"""Test creating uniform cubic grid from molecule against h2o example."""
        # replace this test with a better one later
        pseudo_numbers = np.array([8.0, 1.0, 1.0, 8.0, 1.0, 1.0])
        coordinates = np.array(
            [
                [-1.01306328e-03, 2.87066713e00, -1.97656750e-16],
                [1.74795831e-01, 1.04876344e00, -7.33275045e-17],
                [1.70493824e00, 3.49056186e00, -2.51209193e-16],
                [-1.01306328e-03, -2.62839035e00, 1.80987402e-16],
                [-9.31762597e-01, -3.23876982e00, 1.43814244e00],
                [-9.31762597e-01, -3.23876982e00, -1.43814244e00],
            ]
        )
        grid = UniformCubicGrid.from_molecule(
            pseudo_numbers, coordinates, spacing=2.0, extension=0.0, rotate=True
        )
        expected = np.array(
            [
                [-2.31329824e00, -2.00000000e00, 3.82735565e00],
                [-2.31329824e00, -4.99999997e-09, 3.82735565e00],
                [-3.19696330e-01, -2.00000000e00, 3.98720381e00],
                [-3.19696330e-01, -4.99999997e-09, 3.98720381e00],
                [-2.15345008e00, -2.00000000e00, 1.83375375e00],
                [-2.15345008e00, -4.99999997e-09, 1.83375375e00],
                [-1.59848169e-01, -2.00000000e00, 1.99360191e00],
                [-1.59848169e-01, -4.99999997e-09, 1.99360191e00],
                [-1.99360191e00, -2.00000000e00, -1.59848162e-01],
                [-1.99360191e00, -4.99999997e-09, -1.59848162e-01],
                [-6.77400003e-09, -2.00000000e00, 0.00000000e00],
                [-6.77400003e-09, -4.99999997e-09, 0.00000000e00],
                [-1.83375375e00, -2.00000000e00, -2.15345007e00],
                [-1.83375375e00, -4.99999997e-09, -2.15345007e00],
                [1.59848155e-01, -2.00000000e00, -1.99360191e00],
                [1.59848155e-01, -4.99999997e-09, -1.99360191e00],
            ]
        )
        assert_allclose(grid.points, expected, rtol=1.0e-7, atol=1.0e-7)
