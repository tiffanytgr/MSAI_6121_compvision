import pathlib
import pycolmap

IMAGE_PATH: pathlib.Path = pathlib.Path.cwd() / "image"
OUTPUT_PATH: pathlib.Path = pathlib.Path.cwd() / "output"

OUTPUT_PATH.mkdir()
mvs_path = OUTPUT_PATH / "mvs"
database_path = OUTPUT_PATH / "signpost.db"

pycolmap.extract_features(database_path=database_path, image_path=IMAGE_PATH, camera_model='OPENCV')
pycolmap.match_exhaustive(database_path=database_path)
maps = pycolmap.incremental_mapping(database_path=database_path, image_path=IMAGE_PATH, output_path=OUTPUT_PATH)
maps[0].write(OUTPUT_PATH)
maps[0].write_text(OUTPUT_PATH)
maps[0].export_PLY(OUTPUT_PATH / "mapped.ply")

pycolmap.undistort_images(output_path=mvs_path, input_path=OUTPUT_PATH, image_path=IMAGE_PATH)
pycolmap.patch_match_stereo(workspace_path=mvs_path)  # requires compilation with CUDA

pycolmap.stereo_fusion(output_path=mvs_path / "dense.ply", workspace_path=mvs_path)
pycolmap.poisson_meshing(input_path=mvs_path / "dense.ply", output_path=mvs_path / "meshed-poisson.ply")

