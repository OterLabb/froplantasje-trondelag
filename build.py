"""Assemble map/index.html + map/data/sites_*.geojson from the latest analysis outputs.

    python map/build.py
"""
import json, os, subprocess, sys, tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "map")
D = os.path.join(ROOT, "data", "derived")
OGR = r"C:\OSGeo4W\bin\ogr2ogr.exe"
ENV = dict(os.environ, GDAL_DATA=r"C:\OSGeo4W\share\gdal", PROJ_LIB=r"C:\OSGeo4W\share\proj")

def export(src, dst, simplify):
    if os.path.exists(dst):
        os.remove(dst)
    sql = ("SELECT *, ROUND(ST_X(ST_Centroid(geom))) AS cx, ROUND(ST_Y(ST_Centroid(geom))) AS cy FROM sites")
    r = subprocess.run([OGR, "-f", "GeoJSON", "-t_srs", "EPSG:4326", "-lco", "COORDINATE_PRECISION=5", "-lco", "RFC7946=YES",
                        "-simplify", str(simplify), "-dialect", "sqlite", "-sql", sql, dst, src],
                       env=ENV, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-1500:])
    print(f"{dst}: {os.path.getsize(dst) / 1e6:.1f} MB")

def method(rules_path):
    c = tomllib.load(open(rules_path, "rb"))
    ex = [e["name"] for e in c["exclude"] if e.get("enabled", True)]
    return (f"Every 10 m cell: slope at most {c['slope']['max_deg']}°, elevation at most {c['elevation']['max_m']} m. Each site "
            f"is at least {c['site']['min_area_m2'] / 1e4:g} ha, with some part within {c['roads']['start_within_m']} m of a road "
            f"and none further than {c['roads']['max_distance_m']} m (car, forest and tractor roads). "
            f"Excluded: {'; '.join(ex)}. Rules file: analysis/rules_froplantasje.toml.")

def main():
    if "--html" not in sys.argv: export(os.path.join(D, "sites_froplantasje.gpkg"), os.path.join(M, "data", "sites_froplantasje.geojson"), 5)
    # export(os.path.join(D, "sites.gpkg"), os.path.join(M, "data", "sites_planting.geojson"), 15)
    html = open(os.path.join(M, "template.html"), encoding="utf-8").read()
    html = html.replace("/*LEAFLET_CSS*/", open(os.path.join(M, "vendor", "leaflet.css"), encoding="utf-8").read())
    html = html.replace('/*METHOD*/""', json.dumps(method(os.path.join(ROOT, "analysis", "rules_froplantasje.toml")), ensure_ascii=False))
    # full document for a normal web host (the artifact viewer used to add this wrapper)
    head, body = html.split('<div class="app">', 1)
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<style>body{margin:0}[hidden]{display:none!important}</style>\n'
            f'{head}</head>\n<body>\n<div class="app">{body}</body>\n</html>\n')
    open(os.path.join(M, "index.html"), "w", encoding="utf-8").write(html)
    print("map/index.html written")

if __name__ == "__main__":
    main()
