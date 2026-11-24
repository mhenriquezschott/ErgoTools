"""Rebuild touch-rotation anatomy frames from the packaged desktop STL assets.

Developer-only VTK/Pillow tooling runs in the existing desktop environment. Android
ships only rendered PNGs; it imports no VTK, receives no new dependency and computes
no anatomy or risk. Positions/transform match the desktop anatomical renderer.
"""

import math
from pathlib import Path

import numpy as np
import vtk
from PIL import Image
from vtk.util.numpy_support import vtk_to_numpy

# Existing original component positions, in STL model coordinates.
MODELS = (
    ("human", "body_avatar.stl", (0, 0, 0)),
    ("back", "lower_back.stl", (284, 293, 1010)),
    ("left_arm", "left_forearm.stl", (264.7, 57.9, 851.6)),
    ("left_hand", "left_hand.stl", (369, -42, 694)),
    ("right_arm", "right_forearm.stl", (264.7, 535, 851.6)),
    ("right_hand", "right_hand.stl", (222, 545, 703)),
    ("left_shoulder", "left_shoulder.stl", (247, 105, 1110)),
    ("right_shoulder", "right_shoulder.stl", (247, 495, 1110)),
)
# Stable desktop tool-region mapping; masks only color visible anatomy.
REGIONS = {
    "lifft": ("back",),
    "duet": ("left_arm", "left_hand", "right_arm", "right_hand"),
    "tst": ("left_shoulder", "right_shoulder"),
}


def render() -> None:
    """Render 72 depth-correct views and tintable region masks with fixed framing.

    Args:
        None; paths are anchored to this prototype, never the reference checkout.

    Returns:
        None; reproducible assets are written inside the prototype asset directory.
    """
    root = Path(__file__).resolve().parents[3]
    destination = root / "prototypes/android_demo/src/assets/anatomy"
    destination.mkdir(parents=True, exist_ok=True)
    renderer = vtk.vtkRenderer()
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetMultiSamples(0)
    window.SetSize(480, 560)
    window.AddRenderer(renderer)
    transform = vtk.vtkTransform()
    transform.RotateX(-90)
    transform.RotateZ(-45)
    actors = {}
    for key, filename, position in MODELS:
        reader = vtk.vtkSTLReader()
        reader.SetFileName(str(root / "src/ergotools/resources/models" / filename))
        reader.Update()
        mapper = vtk.vtkPolyDataMapper()
        normals = vtk.vtkPolyDataNormals()
        clean = vtk.vtkCleanPolyData()
        clean.SetInputData(reader.GetOutput())
        clean.ToleranceIsAbsoluteOn()
        clean.SetAbsoluteTolerance(0.25)
        holes = vtk.vtkFillHolesFilter()
        holes.SetInputConnection(clean.GetOutputPort())
        holes.SetHoleSize(18)
        smooth = vtk.vtkWindowedSincPolyDataFilter()
        smooth.SetInputConnection(holes.GetOutputPort())
        smooth.SetNumberOfIterations(20)
        smooth.SetPassBand(0.05)
        smooth.BoundarySmoothingOff()
        smooth.FeatureEdgeSmoothingOff()
        smooth.NormalizeCoordinatesOn()
        normals.SetInputConnection(
            smooth.GetOutputPort() if key == "human" else clean.GetOutputPort()
        )
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        normals.SplittingOff()
        normals.ComputePointNormalsOn()
        normals.Update()
        if key == "human":
            mapper.SetInputData(normals.GetOutput())
        else:
            # Tiny outward offset keeps the original region surfaces above the
            # smoothed display mesh, avoiding depth speckles without x-ray masks.
            surface = vtk.vtkPolyData()
            surface.DeepCopy(normals.GetOutput())
            surface.GetPointData().SetVectors(surface.GetPointData().GetNormals())
            outward = vtk.vtkWarpVector()
            outward.SetInputData(surface)
            outward.SetScaleFactor(1.5)
            outward.Update()
            mapper.SetInputData(outward.GetOutput())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*position)
        actor.SetUserTransform(transform)
        renderer.AddActor(actor)
        actors[key] = actor
    bounds = actors["human"].GetBounds()
    center = [(bounds[i] + bounds[i + 1]) / 2 for i in (0, 2, 4)]
    height = bounds[3] - bounds[2]
    # Upper-body portrait: head, torso and hands; lower legs intentionally out of view.
    center[1] += height * 0.18
    camera = renderer.GetActiveCamera()
    camera.ParallelProjectionOn()
    camera.SetParallelScale(height * 0.34)
    camera.SetViewUp(0, 1, 0)
    grab = vtk.vtkWindowToImageFilter()
    grab.SetInput(window)
    grab.ReadFrontBufferOff()
    depth_grab = vtk.vtkWindowToImageFilter()
    depth_grab.SetInput(window)
    depth_grab.SetInputBufferTypeToZBuffer()
    depth_grab.ReadFrontBufferOff()
    for frame in range(72):
        angle = math.radians(frame * 5)
        camera.SetPosition(
            center[0] + math.sin(angle) * height * 3,
            center[1] + 20,
            center[2] + math.cos(angle) * height * 3,
        )
        camera.SetFocalPoint(*center)
        renderer.ResetCameraClippingRange()
        renderer.SetBackground(0.035, 0.13, 0.22)
        for key, actor in actors.items():
            actor.SetVisibility(key == "human")
            prop = actor.GetProperty()
            prop.SetColor(0.78, 0.85, 0.90)
            prop.SetAmbient(0.42)
            prop.SetDiffuse(0.55)
            prop.SetSpecular(0.035)
            prop.SetSpecularPower(24)
        window.Render()
        grab.Modified()
        grab.Update()
        data = (
            vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars())
            .reshape(560, 480, 3)[::-1]
            .copy()
        )
        rgba_base = np.concatenate(
            [data, np.full((560, 480, 1), 255, dtype=np.uint8)], axis=2
        )
        rgba_base[:, :, 3] = np.where(np.all(data == data[0, 0], axis=2), 0, 255)
        fade = np.minimum(1, (559 - np.arange(560)) / 65).clip(0, 1)
        rgba_base[:, :, 3] = (rgba_base[:, :, 3] * fade[:, None]).astype(np.uint8)
        Image.fromarray(rgba_base).save(
            destination / f"body_{frame:02}.png", optimize=True
        )
        depth_grab.Modified()
        depth_grab.Update()
        human_depth = (
            vtk_to_numpy(depth_grab.GetOutput().GetPointData().GetScalars())
            .reshape(560, 480)[::-1]
            .copy()
        )
        renderer.SetBackground(0, 0, 0)
        for kind, keys in REGIONS.items():
            for key, actor in actors.items():
                actor.SetVisibility(key in keys or (key == "human" and kind != "lifft"))
                prop = actor.GetProperty()
                prop.SetColor((1, 1, 1) if key in keys else (0, 0, 0))
                prop.SetAmbient(1)
                prop.SetDiffuse(0)
                prop.SetSpecular(0)
            window.Render()
            grab.Modified()
            grab.Update()
            mask = (
                vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars())
                .reshape(560, 480, 3)[::-1]
                .copy()
            )
            if kind == "lifft":
                # The display torso intersects the original lower-back overlay.
                # A small world-space decal allowance removes surface islands;
                # the opposite torso surface still occludes the region normally.
                depth_grab.Modified()
                depth_grab.Update()
                region_depth = (
                    vtk_to_numpy(depth_grab.GetOutput().GetPointData().GetScalars())
                    .reshape(560, 480)[::-1]
                    .copy()
                )
                near, far = camera.GetClippingRange()
                visible = (human_depth < 1) & (
                    (region_depth - human_depth) * (far - near) <= 12
                )
                mask[~visible] = 0
            # Keep visible-region alpha separate from lighting: tint multiplies
            # these shaded RGB values instead of replacing them with flat paint.
            for key, actor in actors.items():
                prop = actor.GetProperty()
                prop.SetAmbient(0.35 if key in keys else 1)
                prop.SetDiffuse(0.65 if key in keys else 0)
                prop.SetSpecular(0.08 if key in keys else 0)
            window.Render()
            grab.Modified()
            grab.Update()
            shaded = (
                vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars())
                .reshape(560, 480, 3)[::-1]
                .copy()
            )
            rgba = np.concatenate(
                [shaded, np.full((560, 480, 1), 255, dtype=np.uint8)], axis=2
            )
            rgba[:, :, 3] = (mask[:, :, 0] * fade[:, None]).astype(np.uint8)
            Image.fromarray(rgba).save(
                destination / f"{kind}_{frame:02}.png", optimize=True
            )
    window.Finalize()


if __name__ == "__main__":
    render()
