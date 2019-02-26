import subprocess
import sys
import difflib
import argparse
import json
import random
from geoserver.catalog import Catalog

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

def get_layers(geoserver_username, geoserver_password, geoserver_server, geoserver_ws):
    curl_string = f"curl -v -u \"{geoserver_username}\":\"{geoserver_password}\" -X GET \"{geoserver_server}/layers.json\" -H  \"accept: text/html\" -H  \"content-type: application/json\""
    readout = subprocess.Popen(curl_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1).communicate()[0]
    layers_in_ws = []
    readout = json.loads(readout)['layers']['layer']
    for l in readout:
        layername=l['name']
        layers_in_ws.append(layername)
    return layers_in_ws


if __name__ == '__main__':
    args = setup_cmd_args()

    if not args.geoserver.find("geoserver/rest")>0:
        args.geoserver = args.geoserver+"/geoserver/rest/"

    cat = Catalog(args.geoserver, args.gs_user, args.gs_passw)

    if args.selfdriven:
        layerslist = get_layers(args.gs_user,args.gs_passw, args.geoserver, args.workspace)
        grouplist = []
        with open(args.layerslist,"w") as g:
            for i in layerslist:
                similarname = []
                print(len(layerslist))
                for f in layerslist:
                    similarity = difflib.SequenceMatcher(None, i, f).ratio()
                    if similarity>0.8:
                        similarname.append(f)
                        layerslist.remove(f)
                grouplist.append(list(set(similarname)))
            g.write(str(grouplist))

        layers_in_ws = []
        styles_in_ws = []
        for gl in grouplist:
            ws = get_layer_workspace(args.gs_user, args.gs_passw, args.geoserver, list(gl)[0])
            if ws == args.workspace:
                styles = []
                rlayers = []
                layers_in_ws.append(list(gl))
                for liws in list(gl):
                    that_layer = cat.get_layer(liws)
                    style = that_layer.default_style
                    styles.append(style.name)
                styles_in_ws.append(styles)
        i=0
        lg_names = []
        for lg in layers_in_ws:
            match_strg = lg[0]
            for string in lg:
                similarity = difflib.SequenceMatcher(None, string, match_strg).get_matching_blocks()
                match_strings=[]
                for match in similarity:
                    match_strings.append(string[match.a:match.a + match.size])
                match_strg = match_strings[0]
            lg_name = match_strings[0] + f'{random.randrange(1, 10**3):03}'
            try:
                lg = cat.create_layergroup(lg_name, lg, styles_in_ws[i], workspace=args.workspace)
                cat.save(lg)
            except:
                sys.stderr.write("Some problem occurred when trying to create the layergroup. Please review the input parameters.")
            print(f"Layer group {lg_name} successfully created in {args.geoserver}!")
            i = i+1
    else:
        with open(args.layerslist, "r") as ll:
            layers = ll.readlines()
        layers = list(map(lambda x: x.strip(), layers))
        lg_name = args.layergroupname
        styles = []
        for liws in layers:
            that_layer = cat.get_layer(liws)
            style = that_layer.default_style
            styles.append(style.name)
        try:
            lg = cat.create_layergroup(lg_name, layers, styles, workspace=args.workspace)
            cat.save(lg)
        except:
            sys.stderr.write("Some problem occurred when trying to create the layergroup. Please review the input parameters.")
        print(f"Layer group {lg_name} successfully created in {args.geoserver}!")



