"""Turn stored geometry into SVG path data and points for the templates (y axis down)."""


def path_data(polygon):
    """SVG path `d` for a polygon, one closed subpath per ring."""
    if polygon is None:
        return ''
    return ' '.join(
        'M ' + ' L '.join(f'{x:.1f} {y:.1f}' for x, y in ring.coords[:-1]) + ' Z'
        for ring in polygon
    )


def keypoint_marks(keypoints, field='point_px'):
    """[{'name', 'x', 'y'}] for each key point that has the given coordinates."""
    marks = []
    for keypoint in keypoints:
        point = getattr(keypoint, field)
        if point is not None:
            marks.append({'name': keypoint.name.replace('_', ' '), 'x': point.x, 'y': point.y})
    return marks
