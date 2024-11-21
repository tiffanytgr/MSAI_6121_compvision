import shutil
from pathlib import Path
import subprocess
import enlighten
import pycolmap
from pycolmap import logging


def run_command(command):
    """Run a shell command and print its output."""
    print(f"Running command: {command}")
    process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(process.stdout.decode())
    print(process.stderr.decode())


def incremental_mapping_with_pbar(database_path, image_path, sfm_path):
    """Run incremental mapping with a progress bar."""
    num_images = pycolmap.Database(database_path).num_images
    with enlighten.Manager() as manager:
        with manager.counter(
            total=num_images, desc="Images registered:"
        ) as pbar:
            pbar.update(0, force=True)
            reconstructions = pycolmap.incremental_mapping(
                database_path,
                image_path,
                sfm_path,
                initial_image_pair_callback=lambda: pbar.update(2),
                next_image_callback=lambda: pbar.update(1),
            )
    return reconstructions


def save_points3D_to_ply(reconstruction, ply_output_path):
    """Save the 3D points from the reconstruction to a .ply file."""
    points = reconstruction.points3D.values()
    with open(ply_output_path, "w") as ply_file:
        # Write PLY header
        ply_file.write("ply\n")
        ply_file.write("format ascii 1.0\n")
        ply_file.write(f"element vertex {len(points)}\n")
        ply_file.write("property float x\n")
        ply_file.write("property float y\n")
        ply_file.write("property float z\n")
        ply_file.write("property uchar red\n")
        ply_file.write("property uchar green\n")
        ply_file.write("property uchar blue\n")
        ply_file.write("end_header\n")

        # Write point data
        for point in points:
            x, y, z = point.xyz
            r, g, b = point.color
            ply_file.write(f"{x} {y} {z} {int(r)} {int(g)} {int(b)}\n")


def run():
    # Paths for your images and outputs
    image_path = Path("NTU_CCDS_Signpost")  # Folder containing your images
    output_path = Path("output/")  # Output directory
    database_path = output_path / "database.db"
    sfm_path = output_path / "sfm"
    dense_path = output_path / "dense"
    sparse_ply_output = sfm_path / "sparse_model.ply"
    dense_ply_output = dense_path / "fused.ply"

    # Ensure output directories exist
    output_path.mkdir(exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    # Initialize logging
    logging.set_log_destination(logging.INFO, output_path / "INFO.log.")

    # Step 1: Feature Extraction
    print("Step 1: Extracting features...")
    pycolmap.extract_features(database_path, image_path)

    # Step 2: Feature Matching
    print("Step 2: Matching features...")
    pycolmap.match_exhaustive(database_path)

    # Step 3: Incremental Mapping
    print("Step 3: Running incremental mapping...")
    if sfm_path.exists():
        shutil.rmtree(sfm_path)
    sfm_path.mkdir(exist_ok=True)

    reconstructions = incremental_mapping_with_pbar(database_path, image_path, sfm_path)

    # Export sparse model as a .ply file
    for idx, rec in reconstructions.items():
        print(f"Reconstruction #{idx} summary:\n{rec.summary()}")
        print(f"Saving sparse point cloud as .ply file: {sparse_ply_output}")
        save_points3D_to_ply(rec, sparse_ply_output)  # Save 3D points to .ply file
        break  # Save only the first reconstruction

    print("Sparse reconstruction completed and .ply file saved!")

    # Step 4: Dense Reconstruction Using COLMAP CLI
    print("Step 4: Running dense reconstruction...")
    if dense_path.exists():
        shutil.rmtree(dense_path)
    dense_path.mkdir(exist_ok=True)

    # Undistort images
    run_command(
        f"colmap image_undistorter "
        f"--image_path {image_path} "
        f"--input_path {sfm_path}/0 "
        f"--output_path {dense_path} "
        f"--output_type COLMAP"
    )

    # Dense stereo
    run_command(
        f"colmap patch_match_stereo "
        f"--workspace_path {dense_path} "
        f"--workspace_format COLMAP "
        f"--PatchMatchStereo.geom_consistency true"
    )

    # Stereo fusion
    run_command(
        f"colmap stereo_fusion "
        f"--workspace_path {dense_path} "
        f"--workspace_format COLMAP "
        f"--input_type geometric "
        f"--output_path {dense_ply_output}"
    )

    print(f"Dense reconstruction completed and saved to: {dense_ply_output}")


if __name__ == "__main__":
    run()
