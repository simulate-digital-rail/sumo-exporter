def get_sumo_junction_xml(point):
    return f"<node id=\"{point.id}\" x=\"{point.x}\" y=\"{point.y}\" type=\"priority\"/>"


def get_sumo_signal_xml(signal):
    return f"<node id=\"{signal.id}\" x=\"{signal.x}\" y=\"{signal.y}\" type=\"rail_signal\"/>"


def get_sumo_edge_xml(track):
    shape_coords = " ".join(track.shape_coordinates)
    shape_coords_re = " ".join(reversed(track.shape_coordinates))
    return "\n".join([f"<!-- Track {track.top_kante_uuid} -->",
                      f"<edge id=\"{track.id}\" from=\"{track.left_point.id}\" to=\"{track.right_point.id}\" shape=\"{shape_coords}\" priority=\"-1\" numLanes=\"1\" speed=\"110.0\" allow=\"rail rail_electric\" spreadType=\"center\" />",
                      f"<edge id=\"{track.re_id}\" from=\"{track.right_point.id}\" to=\"{track.left_point.id}\" shape=\"{shape_coords_re}\" priority=\"-1\" numLanes=\"1\" speed=\"110.0\" allow=\"rail rail_electric\" spreadType=\"center\" />"])


def get_sumo_point_connection_xml(point):
    if point.left is not None and point.right is not None:
        return "\n".join([f"<!-- Point {point.id} {point.top_knoten_uuid} -->",
                          f"<connection from=\"{point.left.id}\" to=\"{point.head.id}\"/>",
                          f"<connection from=\"{point.left.id}\" to=\"{point.head.re_id}\"/>",
                          f"<connection from=\"{point.left.re_id}\" to=\"{point.head.id}\"/>",
                          f"<connection from=\"{point.left.re_id}\" to=\"{point.head.re_id}\"/>",
                          f"<connection from=\"{point.right.id}\" to=\"{point.head.id}\"/>",
                          f"<connection from=\"{point.right.id}\" to=\"{point.head.re_id}\"/>",
                          f"<connection from=\"{point.right.re_id}\" to=\"{point.head.id}\"/>",
                          f"<connection from=\"{point.right.re_id}\" to=\"{point.head.re_id}\"/>",
                          f"<connection from=\"{point.head.id}\" to=\"{point.left.id}\"/>",
                          f"<connection from=\"{point.head.id}\" to=\"{point.right.id}\"/>",
                          f"<connection from=\"{point.head.id}\" to=\"{point.left.re_id}\"/>",
                          f"<connection from=\"{point.head.id}\" to=\"{point.right.re_id}\"/>",
                          f"<connection from=\"{point.head.re_id}\" to=\"{point.left.id}\"/>",
                          f"<connection from=\"{point.head.re_id}\" to=\"{point.right.id}\"/>",
                          f"<connection from=\"{point.head.re_id}\" to=\"{point.left.re_id}\"/>",
                          f"<connection from=\"{point.head.re_id}\" to=\"{point.right.re_id}\"/>"])
    else:  # Dead End
        return ""


def get_sumo_signal_connection_xml(signal):
    return "\n".join([f"<!-- Signal {signal.id} {signal.signal_uuid} -->",
                      f"<connection from=\"{signal.left_track.id}\" to=\"{signal.right_track.id}\"/>",
                      f"<connection from=\"{signal.left_track.id}\" to=\"{signal.right_track.re_id}\"/>",
                      f"<connection from=\"{signal.left_track.re_id}\" to=\"{signal.right_track.id}\"/>",
                      f"<connection from=\"{signal.left_track.re_id}\" to=\"{signal.right_track.re_id}\"/>",
                      f"<connection from=\"{signal.right_track.id}\" to=\"{signal.left_track.id}\"/>",
                      f"<connection from=\"{signal.right_track.id}\" to=\"{signal.left_track.re_id}\"/>",
                      f"<connection from=\"{signal.right_track.re_id}\" to=\"{signal.left_track.id}\"/>",
                      f"<connection from=\"{signal.right_track.re_id}\" to=\"{signal.left_track.re_id}\"/>"])


def get_sumo_route_xml(route):
    track_ids = " ".join(route.track_ids)
    return (f"<route edges=\"{track_ids}\" color=\"{route.color}\" id=\"{route.id}\">"
            f"\n\t\t<stop lane=\"{route.track_ids[-1]}_0\" duration=\"7200\"/>"
            f"\n\t</route>")


def get_routes_boilerplate_xml(routes_as_xml):
    file_content = ['<?xml version="1.0" encoding="UTF-8"?>',
                    '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
                    "\t" + "\n\t".join(routes_as_xml),
                    "\n\t<vType id=\"regio\" accel=\"2.5\" decel=\"1.3\" length=\"20.00\" vClass=\"rail\" color=\"193,18,28\" />",
                    "\n\t<vType id=\"ice\" accel=\"5\" decel=\"1.3\" length=\"60.00\" vClass=\"rail_electric\" color=\"192,192,192\" />",
                    "\n\t<vType id=\"cargo\" accel=\"2.5\" decel=\"1.3\" length=\"80.00\" vClass=\"rail\" color=\"30,30,30\" />",
                    "\n</routes>"]
    return "\n".join(file_content)


def get_sumocfg_boilerplate_xml(net_file_name, routes_file_name):
    file_content = [
                    "<configuration>",
                    "\t<input>",
                    f"\t\t<net-file value=\"{net_file_name}\" />",
                    f"\t\t<route-files value=\"{routes_file_name}\" />",
                    # "\t\t<additional-files value=\"reroutes.add.xml\" />",
                    "\t</input>",
                    "</configuration>"
                    ]
    return "\n".join(file_content)
