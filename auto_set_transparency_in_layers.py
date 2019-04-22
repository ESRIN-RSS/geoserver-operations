import subprocess
import argparse
import json


def setup_cmd_args():
    """Setup command line arguments."""
    parser = argparse.ArgumentParser(description="Automatically create layergroups in geoserver. This includes 2 different methods:\n1)self driven organization - the script will  "
                                                 "organize groups of layers based on the similarity between the layer names and assign a layer group name for each group based on the common characters between the layers names in the group.\n\nExample: auto_group_layers.py http://maps.eo.esa.int/geoserver/rest/ --gs_user geoserver_username --gs_passw geoserver_pw --layerslist c:\\temp\\layerslist.txt --selfdriven --workspace APOLLO\n\n"
                                                 "2)manual input - The layer list and layer group name is assigned manually in the arguments.\n\nExample: auto_group_layers.py http://maps.eo.esa.int/geoserver/rest/ --gs_user geoserver_username --gs_passw geoserver_pw --layerslist c:\\temp\layerslist.txt --layergroupname teste --workspace APOLLO\n", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("geoserver", help="Geoserver server")
    parser.add_argument("--layerslist", help="Folder to write/read the layer list.",
                        default="c:\\temp\out_test_group.txt")
    parser.add_argument("--workspace", help="Set Workspace manually")
    parser.add_argument("--layergroupname", help="Set layergroupname manually")
    parser.add_argument("--gs_user", help="Geoserver username", required=True)
    parser.add_argument("--gs_passw", help="Geoserver password", required=True)
    parser.add_argument("-sd","--selfdriven", action='store_true', help="Self driven organization")
    return parser.parse_args()


def get_layer_workspace(geoserver_username, geoserver_password, geoserver_server, layername):
    curl_string = "curl -v -u "+geoserver_username+":"+geoserver_password+" -GET \""+geoserver_server+"/layers/"+layername+".json\""
    readout = subprocess.Popen(curl_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1).communicate()[0]
    try:
        readout = json.loads(readout)['layer']['resource']['href']
        workspace = readout.split("/")[readout.split("/").index('workspaces')+1]
    except:
        workspace = ""
    return workspace


def set_transparent_color(geoserver_username, geoserver_password, geoserver_server, geoserver_ws, layer_name):
    curl_string = f"curl -u \"{geoserver_username}\":\"{geoserver_password}\" -v -XPUT -H \"Content-type: text/xml\" -d \"<coverage><parameters><entry><string>InputTransparentColor</string><string>#FFFFFF</string></entry></parameters><enabled>true</enabled></coverage>\" {geoserver_server}/workspaces/{geoserver_ws}/coveragestores/{layer_name}/coverages/{layer_name}.xml"
    print(curl_string)
    # readout = subprocess.Popen(curl_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1).communicate()[0]
    result = subprocess.run(curl_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if result.returncode == 0:
        return result.stdout
    else:
        if result.stderr:
            print('Preprocess failed: ')
            print(result.stderr)

        return ''


if __name__ == '__main__':
    args = setup_cmd_args()

    if not args.geoserver.find("geoserver/rest")>0:
        args.geoserver = args.geoserver+"/geoserver/rest/"

    with open(args.layerslist, "r") as ll:
        layers = ll.readlines()
    layers = list(map(lambda x: x.strip(), layers))
    for liws in layers:
        ws = get_layer_workspace(args.gs_user, args.gs_passw, args.geoserver, liws)
        set_transparent_color(args.gs_user, args.gs_passw, args.geoserver, ws, liws)


