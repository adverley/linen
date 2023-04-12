from typing import Tuple

import numpy as np
from airo_typing import Vector3DType

from linen.geometry.orientation import flat_orientation, pitch_gripper_orientation
from linen.geometry.project import project_point_on_line
from linen.path.circular_arc import circular_arc_orientation_path, circular_arc_position_trajectory
from linen.path.combine import combine_orientation_and_position_paths
from linen.path.slerp import slerp_trajectory


def circular_fold_middle_orientation(approach_direction: Vector3DType, fold_line_direction: Vector3DType):
    start_orientation_flat = flat_orientation(approach_direction)

    orientation_path = circular_arc_orientation_path(start_orientation_flat, fold_line_direction, np.pi)
    middle_orientation = orientation_path(np.pi / 2)
    return middle_orientation


def circular_fold_trajectory(
    grasp_location: Vector3DType,
    approach_direction: Vector3DType,
    fold_line: Tuple[Vector3DType, Vector3DType],
    start_pitch_angle: float = np.pi / 4,
    end_pitch_angle: float = np.pi / 4,
    end_height_offset: float = 0.04,
    speed: float = 0.25,
):
    grasp_projected = project_point_on_line(grasp_location, fold_line)
    radius = np.linalg.norm(grasp_projected - grasp_location)
    angle_delta = np.arcsin(end_height_offset / radius)
    max_angle = np.pi - angle_delta

    position_trajectory = circular_arc_position_trajectory(grasp_location, *fold_line, max_angle, speed)

    _, fold_line_direction = fold_line
    middle_orientation = circular_fold_middle_orientation(approach_direction, fold_line_direction)

    start_orientation_flat = flat_orientation(approach_direction)
    start_orientation = pitch_gripper_orientation(start_orientation_flat, -start_pitch_angle)
    end_orientation = pitch_gripper_orientation(start_orientation_flat, end_pitch_angle - np.pi)

    orientations = [start_orientation, middle_orientation, end_orientation]
    times = [0, position_trajectory.duration / 2, position_trajectory.duration]
    orientation_trajectory = slerp_trajectory(times, orientations)

    pose_trajectory = combine_orientation_and_position_paths(orientation_trajectory, position_trajectory)
    return pose_trajectory