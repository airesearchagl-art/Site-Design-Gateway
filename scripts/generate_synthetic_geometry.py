"""Recreate the two public fixtures from invented coordinates, never runtime data.

Run from an editable checkout: python scripts/generate_synthetic_geometry.py
Only the two declared synthetic fixture paths are replaced.
"""
import io
import json
from pathlib import Path

from bve.geometry._dxf_runtime import ezdxf_module, quiet_dxf

RING_M = [(0, 0), (10, 0), (12, 10), (6, 20), (0, 20)]


def synthetic_files() -> dict[str, bytes]:
    feature = {"type": "Feature", "properties": {"unit": "m", "coordinateSystem": "local_xy",
                                                "sourceStatus": "assumed"},
               "geometry": {"type": "Polygon", "coordinates": [[*RING_M, RING_M[0]]]}}
    with quiet_dxf():
        ezdxf = ezdxf_module()
        previous = ezdxf.options.write_fixed_meta_data_for_testing
        ezdxf.options.write_fixed_meta_data_for_testing = True
        try:
            doc = ezdxf.new("R2010", units=4)
            doc.layers.new("SITE")
            doc.modelspace().add_lwpolyline([(x * 1000, y * 1000) for x, y in RING_M],
                                          close=True, dxfattribs={"layer": "SITE"})
            stream = io.StringIO()
            doc.write(stream)
            dxf = stream.getvalue().encode("utf-8")
        finally:
            ezdxf.options.write_fixed_meta_data_for_testing = previous
    return {"site.geojson": (json.dumps(feature, indent=2) + "\n").encode("utf-8"), "site.dxf": dxf}


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "cases/example-urban-office"
    for name, data in synthetic_files().items():
        (target / name).write_bytes(data)
    print("PASS synthetic fixtures generated")
